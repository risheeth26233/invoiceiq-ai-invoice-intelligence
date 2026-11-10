import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO

import pymupdf
from PIL import Image

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 10
MAX_PIXELS = 16_000_000
LABELS = {
    "number": r"(?:Invoice\s*(?:number|no\.?|#)|Invoice\s*:)",
    "vendor": r"(?:Vendor|Supplier|From)",
    "invoice_date": r"(?:Invoice\s+date|Issue\s+date|Date)",
    "due_date": r"Due\s+date",
    "subtotal": r"Sub\s*total",
    "tax": r"(?:Tax(?:\s+amount)?|VAT|GST)",
    "total": r"(?:Grand\s+total|Total(?:\s+(?:due|amount))?|Amount\s+due)",
    "currency": r"Currency",
}


def normalize_date(value):
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value, pattern).date().isoformat()
        except ValueError:
            continue
    match = re.fullmatch(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", value)
    if not match:
        return None
    first, second, year = map(int, match.groups())
    if first <= 12 and second <= 12 and first != second:
        return None
    day, month = (second, first) if second > 12 else (first, second)
    try:
        return date(year, month, day).isoformat()
    except ValueError:
        return None


def parse_fields(source):
    fields = {}
    for key, label in LABELS.items():
        match = re.search(rf"^[ \t]*{label}[ \t]*[:#]?[ \t]+([^\r\n]+)", source, re.I | re.M)
        if not match:
            match = re.search(rf"^[ \t]*{label}[ \t]*:[ \t]*([^\r\n]+)", source, re.I | re.M)
        fields[key] = match.group(1).strip() if match else None
    for key in ("invoice_date", "due_date"):
        fields[key] = normalize_date(fields[key])
    total = fields["total"] or ""
    if not fields["currency"]:
        match = re.search(r"\b(USD|EUR|INR|GBP|CAD|AUD|JPY|CHF)\b", total, re.I)
        fields["currency"] = match.group(1).upper() if match else None
    if fields["currency"]:
        code = fields["currency"].upper()
        fields["currency"] = code if re.fullmatch(r"[A-Z]{3}", code) else None
    for key in ("subtotal", "tax", "total"):
        value = re.sub(r"(?i)\b[A-Z]{3}\b|[$€£₹]", "", fields[key] or "").strip()
        match = re.fullmatch(r"(?:\d{1,12}|\d{1,3}(?:,\d{3}){1,3})(?:\.\d{1,2})?", value)
        fields[key] = format(Decimal(value.replace(",", "")), ".2f") if match else None
    return fields


def read_document(data):
    if data.startswith(b"%PDF-"):
        kind = "pdf"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        kind = "png"
    elif data.startswith(b"\xff\xd8\xff"):
        kind = "jpeg"
    else:
        raise ValueError("Choose a valid PDF, PNG, or JPEG file.")
    try:
        if kind != "pdf":
            with Image.open(BytesIO(data)) as image:
                if image.width * image.height > MAX_PIXELS:
                    raise ValueError("Image exceeds the pixel limit.")
                image.verify()
        with pymupdf.open(stream=data, filetype=kind) as original:
            if original.needs_pass or not 1 <= len(original) <= MAX_PAGES:
                raise ValueError("Use an unlocked invoice with 1 to 10 pages.")
            with pymupdf.open() as converted:
                if kind != "pdf":
                    with pymupdf.open(stream=original.convert_to_pdf(), filetype="pdf") as image_pdf:
                        converted.insert_pdf(image_pdf)
                document = converted if kind != "pdf" else original
                chunks = []
                warnings = []
                used_ocr = False
                for page in document:
                    content = page.get_text(sort=True).strip()
                    if not content:
                        used_ocr = True
                        dpi = 150
                        pixels = page.rect.width * page.rect.height * (dpi / 72) ** 2
                        if pixels > MAX_PIXELS:
                            warnings.append("A page exceeded the OCR pixel limit.")
                        else:
                            try:
                                ocr = page.get_textpage_ocr(dpi=dpi, full=True, tessdata=os.environ.get("TESSDATA_PREFIX"))
                                content = page.get_text(textpage=ocr, sort=True).strip()
                            except (RuntimeError, ValueError):
                                logging.getLogger(__name__).info("OCR failed for a page")
                                warnings.append("OCR could not read a page. Enter missing values manually.")
                    chunks.append(content)
    except (pymupdf.FileDataError, RuntimeError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("The document could not be opened.") from exc
    fields = parse_fields("\n".join(chunks))
    return {
        "fields": fields,
        "confidence": {key: ("missing" if value is None else "review" if used_ocr else "matched")
                       for key, value in fields.items()},
        "warnings": list(dict.fromkeys(warnings)),
    }
