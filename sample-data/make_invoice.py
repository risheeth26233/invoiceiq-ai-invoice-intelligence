from pathlib import Path

import pymupdf


def create_invoice():
    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text((56, 72), "INVOICE", fontsize=24)
        page.insert_text((56, 125), "\n".join((
            "Vendor: Juniper Studio",
            "Invoice number: JS-1042",
            "Invoice date: 2026-10-06",
            "Due date: 2026-11-06",
            "Currency: USD",
            "Subtotal: 120.00",
            "Tax: 9.60",
            "Grand total: USD 129.60",
        )), fontsize=14)
        return document.tobytes(no_new_id=True)


if __name__ == "__main__":
    path = Path(__file__).with_name("juniper-invoice.pdf")
    path.write_bytes(create_invoice())
    print(path)
