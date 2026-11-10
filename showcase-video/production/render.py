"""Render the 120-second demo from real browser footage and timed narration."""
import json
import math
import re
from difflib import SequenceMatcher
import subprocess
import wave
from functools import cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

P = Path(__file__).resolve().parent
OUT = P.parent
W, H, FPS, SR = 1280, 720, 30, 48000
NAVY, DARK, EMERALD = "#102535", "#0b1d29", "#0f765c"
MINT, PAPER, SUB = "#a7f1cf", "#eff7f4", "#496573"
SCENES = json.loads((P / "scenes.json").read_text(encoding="utf-8"))
TOTAL = sum(s["duration"] for s in SCENES)
LIVE = ["dashboard", "upload", "review", "save", "analytics", "duplicate"]
FRAMES, SEGMENTS = P / "frames", P / "segments"


@cache
def font(size, bold=False):
    return ImageFont.truetype("C:/Windows/Fonts/" + ("segoeuib.ttf" if bold else "segoeui.ttf"), size)


def txt(d, x, y, text, size=24, color=NAVY, bold=False):
    for i, line in enumerate(text.splitlines()):
        d.text((x, y + i * size * 1.12), line, font=font(size, bold), fill=color, anchor="lt")


def card(d, box, fill="white", outline=None, radius=18):
    d.rounded_rectangle(box, radius, fill=fill, outline=outline, width=2)


def brand(d, x, y, invert=False):
    card(d, (x, y, x + 45, y + 45), MINT, radius=12)
    txt(d, x + 11, y + 11, "IQ", 20, DARK, True)
    txt(d, x + 58, y + 7, "InvoiceIQ", 26, "white" if invert else NAVY, True)


def tag(d, title, index, dark=False):
    brand(d, 66, 45, dark)
    txt(d, 960, 57, "WEEK 01  /  52 PROJECTS", 18, MINT if dark else EMERALD, True)
    d.line((66, 112, 1214, 112), fill="#33515d" if dark else "#ccded7", width=2)
    txt(d, 68, 137, index + "  /  " + title.upper(), 17, MINT if dark else EMERALD, True)


def doc(d, x, y, label, amount, tilt=0):
    card(d, (x + 5, y + 7, x + 154, y + 177), "#153747", radius=13)
    card(d, (x, y, x + 149, y + 170), "#f2faf6", radius=13)
    card(d, (x + 12, y + 13, x + 62, y + 37), "#c2f4df", radius=7)
    txt(d, x + 19, y + 18, label, 13, EMERALD, True)
    for k in range(3):
        d.line((x + 15, y + 62 + k * 17, x + 114 - k * 12, y + 62 + k * 17), fill="#bbd3cd", width=4)
    txt(d, x + 15, y + 131, amount, 20, NAVY, True)


def draw_problem(d, t):
    tag(d, "The problem", "01", True)
    if t >= 25.3:
        progress = min(1, (t - 25.3) / .65)
        x = 82 + (1 - progress) * 46
        txt(d, x, 258, "Meet InvoiceIQ.", 94, "white", True)
        txt(d, x + 4, 380, "Turn invoices into searchable records.", 34, MINT)
        return
    title, body = (
        ("Invoices keep\ncoming in.", "Different files. Different layouts.")
        if t < 12 else
        ("Then comes\nthe retyping.", "Copy the vendor. Check the total.")
        if t < 19 else
        ("Small errors\nadd up.", "One wrong total. One duplicate.")
    )
    txt(d, 74, 224, title, 69, "white", True)
    txt(d, 78, 401, body, 25, MINT)
    card(d, (695, 196, 1204, 572), "#183847", "#345260", 26)
    # Original vector illustration of a small-business owner at their desk.
    d.rounded_rectangle((741, 347, 856, 469), 39, fill="#1b836c")
    d.ellipse((767, 271, 831, 345), fill="#d5a082")
    d.pieslice((762, 262, 837, 338), 183, 360, fill="#172735")
    d.line((752, 382, 793, 429, 860, 429), fill="#d5a082", width=16, joint="curve")
    card(d, (728, 463, 1177, 493), "#728a80", radius=9)
    card(d, (846, 386, 972, 461), "#9fbbb5", radius=9)
    d.line((842, 462, 977, 462), fill=MINT, width=5)
    if t < 12:
        for k, (x, y, label, amount) in enumerate([
            (867, 224, "PDF", "$129.60"), (1023, 260, "IMG", "$84.00"), (988, 360, "CSV", "$245.25")
        ]):
            if t >= k * 3.1:
                rise = max(0, 1 - (t - k * 3.1) / .65) * 28
                doc(d, x, y + rise + 3 * math.sin(t + k), label, amount)
    else:
        card(d, (841, 209, 1170, 454), "#f2faf6", radius=14)
        txt(d, 859, 226, "INVOICE TRACKER", 17, EMERALD, True)
        d.line((858, 260, 1153, 260), fill="#b9d3cc", width=2)
        txt(d, 863, 276, "Vendor", 17, NAVY, True)
        txt(d, 1052, 276, "Total", 17, NAVY, True)
        n = min(3, int((t - 12) / 1.7) + 1)
        for k, (vendor, amount) in enumerate([("Juniper Studio", "$129.60"), ("Brook Office", "$84.00"), ("Juniper Studio", "$129.60")][:n]):
            y = 309 + k * 42
            card(d, (854, y - 4, 1156, y + 31), "#fce4d8" if t >= 19 and k in (0, 2) else "#def2e8", radius=6)
            txt(d, 864, y + 1, vendor, 16)
            txt(d, 1050, y + 1, amount, 16, NAVY, True)
        if t >= 19:
            txt(d, 852, 510, "Wrong amounts  /  Duplicate entries", 16, "#ffd5bd", True)


def draw_approach(d, t):
    tag(d, "The approach", "02")
    txt(d, 69, 202, "From document to verified record.", 60, NAVY, True)
    txt(d, 72, 292, "Extraction prepares a draft. A person decides what gets saved.", 26, SUB)
    steps = [("01", "Upload", "PDF or image"),
             ("02", "Extract", "PDF text / OCR"),
             ("03", "Review", "Editable fields"),
             ("04", "Save", "Verified record"),
             ("05", "Analyze", "Totals / duplicates")]
    for i, (n, name, line) in enumerate(steps):
        x = 70 + 230 * i
        active = t >= .6 + i * 1.25
        y = 394 + (0 if active else 11)
        card(d, (x, y, x + 209, y + 142), "white" if active else "#e5efeb", "#b4d8cb", 17)
        txt(d, x + 17, y + 18, n, 18, EMERALD, True)
        txt(d, x + 17, y + 48, name, 29, NAVY, True)
        txt(d, x + 17, y + 91, line, 17, SUB)
        if i < len(steps) - 1:
            txt(d, x + 210, y + 58, "›", 25, EMERALD, True)


def draw_limits(d, t):
    tag(d, "What to know", "04")
    txt(d, 70, 201, "Where it helps. Where it stops.", 57, NAVY, True)
    cards = [
        (70, "Advantages", ["Less repetitive data entry", "Editable, human-verified records", "Search, analytics, duplicate warnings", "Local PDF and image extraction"]),
        (653, "Current limitations", ["Accuracy varies by invoice layout", "Some fields need manual correction", "Detailed line items are future work", "Public sample only · free-tier cold starts"]),
    ]
    for x, title, lines in cards:
        card(d, (x, 307, x + 555, 603), "white", "#c8ded4", 22)
        txt(d, x + 25, 330, title, 29, EMERALD if x == 70 else NAVY, True)
        for k, line in enumerate(lines):
            y = 392 + k * 46
            d.ellipse((x + 25, y + 6, x + 36, y + 17), fill=EMERALD if x == 70 else "#c87549")
            txt(d, x + 48, y, line, 22, SUB if t < .6 + k * .5 else NAVY)


def draw_close(d, t):
    tag(d, "52 Weeks. 52 Projects.", "05", True)
    txt(d, 75, 200, "InvoiceIQ", 101, "white", True)
    txt(d, 81, 320, "WEEK 01  /  52", 31, MINT, True)
    txt(d, 83, 411, "LIVE DEMO", 17, MINT, True)
    txt(d, 83, 442, "invoiceiq-demo-risheeth.vercel.app", 30, "white")
    txt(d, 83, 509, "GITHUB", 17, MINT, True)
    txt(d, 83, 541, "github.com/risheeth26233/invoiceiq-ai-invoice-intelligence", 28, "white")


def ff(*args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)], cwd=P, check=True)


def duration(file):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
                                         "format=duration", "-of", "csv=p=0", str(file)], cwd=P))


def motion(scene, target):
    key, length = scene["key"], scene["duration"]
    painter = {"problem": draw_problem, "approach": draw_approach,
               "limits": draw_limits, "close": draw_close}[key]
    bg = DARK if key in {"problem", "close"} else PAPER
    proc = subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
                             "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
                             "-i", "-", "-vf", "scale=1920:1080,setsar=1,format=yuv420p" +
                             (",fade=t=out:st=4.55:d=0.45" if key == "close" else ""),
                             "-c:v", "libx264", "-threads", "4", "-preset", "veryfast", "-crf", "17", str(target)],
                            cwd=P, stdin=subprocess.PIPE)
    try:
        for frame in range(length * FPS):
            im = Image.new("RGB", (W, H), bg)
            d = ImageDraw.Draw(im)
            painter(d, frame / FPS)
            if key != "close":
                d.line((68, 633, 1212, 633), fill="#355361" if bg == DARK else "#cbded5", width=2)
            proc.stdin.write(im.tobytes())
    finally:
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError(f"Could not render {key}")


def browser_shot(scene, target, marks):
    key, length = scene["key"], scene["duration"]
    start, end = marks[key]
    speed = length / (end - start)
    focus = {
        "dashboard": (.035, .42, .32, 1.7),
        "upload": (.055, .68, .50, 5.2),
        "review": (.115, .76, .62, 2.7),
        "save": (.040, .49, .41, 3.7),
        "analytics": (.095, .56, .43, 2.1),
        "duplicate": (.100, .75, .82, 5.0),
    }
    amount, x, y, cue = focus[key]
    ease = "min(min(1,max(0,(on-20)/65)),max(0,(" + str(length * FPS) + "-on)/26))"
    zoom = f"1+{amount}*pow(sin(PI/2*({ease})),2)"
    plate = FRAMES / f"{key}-frame.png"
    label = FRAMES / f"{key}-cue.png"
    ff("-loop", 1, "-framerate", FPS, "-i", plate, "-ss", round(start, 3),
       "-t", round(end - start, 3), "-i", P / "captures/live.webm",
       "-loop", 1, "-framerate", FPS, "-i", label,
       "-filter_complex_threads", 2, "-filter_complex",
       f"[1:v]setpts=(PTS-STARTPTS)*{speed:.7f},fps={FPS},"
       f"tpad=stop_mode=clone:stop_duration=0.5,scale=2880:1620,"
       f"zoompan=z='{zoom}':x='(iw-iw/zoom)*{x}':y='(ih-ih/zoom)*{y}':d=1:s=1600x900:fps={FPS}[site];"
       f"[0:v][site]overlay=160:88[frame];"
       f"[2:v]format=rgba,fade=t=in:st={cue}:d=0.32:alpha=1,"
       f"fade=t=out:st={length-.52}:d=0.36:alpha=1[cue];"
       f"[frame][cue]overlay=x='181-24*max(0,min(1,({cue}+.32-t)/.32))':y=875:"
       f"enable='gte(t,{cue})',setsar=1,format=yuv420p[v]",
       "-map", "[v]", "-t", length, "-an", "-c:v", "libx264", "-threads", 4,
       "-preset", "veryfast", "-crf", 17, target)


def stamp(seconds, ass=False):
    value = round(seconds * (100 if ass else 1000))
    if ass:
        return f"{value//360000}:{value//6000%60:02}:{value//100%60:02}.{value%100:02}"
    return f"{value//3600000:02}:{value//60000%60:02}:{value//1000%60:02},{value%1000:03}"


def cue_lines(entries, speed, start, length, narration):
    words = [item.copy() for item in entries if item.get("type") == "WordBoundary"]
    written = narration.split()
    clean = lambda token: re.sub(r"[^\w]", "", token).casefold()
    matcher = SequenceMatcher(a=[clean(word["text"]) for word in words],
                              b=[clean(token) for token in written], autojunk=False)
    for a, b, count in matcher.get_matching_blocks():
        for k in range(count):
            words[a+k]["text"] = written[b+k]
    for source, target in [
        (["invoice", "iq"], "InvoiceIQ"),
        (["j", "s", "one", "zero", "four", "two"], "JS-1042"),
        (["u", "s"], "US"),
    ]:
        i = 0
        while i + len(source) <= len(words):
            phrase = words[i:i+len(source)]
            if [clean(word["text"]) for word in phrase] == source:
                last = phrase[-1]
                suffix = last["text"][-1] if last["text"].endswith((".", ",", "?", "!")) else ""
                words[i:i+len(source)] = [{
                    "text": target + suffix, "offset": phrase[0]["offset"],
                    "duration": last["offset"] + last["duration"] - phrase[0]["offset"],
                }]
            i += 1
    phrases, group = [], []
    for entry in words:
        group.append(entry)
        if len(group) >= 9 or (len(group) >= 3 and entry["text"].endswith((".", "?", "!", ","))):
            phrases.append(group)
            group = []
    if group:
        if len(group) <= 2 and phrases:
            phrases[-1].extend(group)
        else:
            phrases.append(group)
    for i, words in enumerate(phrases):
        a = .34 + words[0]["offset"] / 1e7 / speed
        end_word = words[-1]["offset"] + words[-1]["duration"]
        b = .34 + end_word / 1e7 / speed + .17
        if i + 1 < len(phrases):
            b = min(b, .34 + phrases[i+1][0]["offset"] / 1e7 / speed - .015)
        phrase = " ".join(word["text"] for word in words).replace("Invoice IQ", "InvoiceIQ")
        yield start + a, start + min(b, length - .08), phrase


def music(output):
    score = np.zeros((TOTAL * SR, 2), dtype=np.float32)
    chords = [(130.81, 164.81, 196, 246.94), (110, 130.81, 164.81, 196),
              (87.31, 130.81, 174.61, 220), (98, 146.83, 196, 220)]
    for i, start in enumerate(range(0, TOTAL, 12)):
        chord = chords[i % len(chords)]
        for k in range(4):
            at = start + k * 3
            t = np.arange(min(7, TOTAL - at) * SR, dtype=np.float32) / SR
            f = chord[(0, 2, 1, 3)[k]] * 2
            env = (1 - np.exp(-t / .24)) * np.exp(-t / 2.1) * np.clip((len(t)/SR - t)/.7, 0, 1)
            tone = (np.sin(2 * np.pi * f * t) + .12 * np.sin(4 * np.pi * f * t)) * env
            pos = at * SR
            pan = .35 if k % 2 else .65
            score[pos:pos+len(t), 0] += tone * pan
            score[pos:pos+len(t), 1] += tone * (1 - pan)
    score *= 10**(-32/20) / np.sqrt(np.mean(score**2))
    fade = np.linspace(0, 1, 3 * SR, dtype=np.float32)[:, None]
    score[:len(fade)] *= fade
    score[-len(fade):] *= fade[::-1]
    with wave.open(str(output), "wb") as wav:
        wav.setparams((2, 2, SR, 0, "NONE", "not compressed"))
        wav.writeframes((score * 32767).astype("<i2").tobytes())


def thumbnail(marks):
    still = FRAMES / "thumb-source.png"
    ff("-ss", marks["analytics"][0] + 4, "-i", P / "captures/live.webm", "-frames:v", 1, still)
    with Image.open(still) as image:
        app = ImageOps.fit(image.convert("RGB"), (702, 395))
    image = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(image)
    tag(d, "Product walkthrough", "01", True)
    txt(d, 68, 229, "InvoiceIQ", 72, "white", True)
    txt(d, 72, 322, "From invoice to\nverified record.", 38, MINT, True)
    txt(d, 74, 468, "LIVE PRODUCT DEMO", 19, MINT, True)
    card(d, (508, 208, 1222, 617), "#5b8c82", radius=12)
    image.paste(app, (514, 215))
    image.resize((1920, 1080), Image.Resampling.LANCZOS).save(OUT / "InvoiceIQ_Thumbnail.png")


def main():
    FRAMES.mkdir(exist_ok=True)
    SEGMENTS.mkdir(exist_ok=True)
    marks = json.loads((P / "captures/marks.json").read_text())
    cues, video_list, audio_list = [], [], []
    offset = 0
    subprocess.run(["node", str(P / "motion-overlay.cjs")], cwd=P, check=True)
    for index, scene in enumerate(SCENES):
        key, length = scene["key"], scene["duration"]
        variant = "-motion" if key in LIVE else ""
        video = SEGMENTS / f"{index:02}-{key}{variant}.mp4"
        if not video.exists() or video.stat().st_size == 0:
            if key in LIVE:
                browser_shot(scene, video, marks)
            else:
                motion(scene, video)
        print(f"Video {index+1}/{len(SCENES)}: {key}", flush=True)
        source = P / "audio" / f"{key}.mp3"
        speed = max(1, duration(source) / (length - .75))
        print(f"  narration rate multiplier {speed:.3f}", flush=True)
        audio = SEGMENTS / f"{index:02}-{key}.wav"
        ff("-i", source, "-af", f"atempo={speed:.6f},adelay=340,apad=whole_dur={length}",
           "-t", length, "-ar", SR, "-ac", 1, "-c:a", "pcm_s16le", audio)
        entries = [json.loads(line) for line in source.with_suffix(".jsonl").read_text(encoding="utf-8").splitlines()]
        cues.extend(cue_lines(entries, speed, offset, length, scene["text"]))
        video_list.append(f"file '{video.name}'")
        audio_list.append(f"file '{audio.name}'")
        offset += length

    (SEGMENTS / "videos.txt").write_text("\n".join(video_list) + "\n")
    (SEGMENTS / "voices.txt").write_text("\n".join(audio_list) + "\n")
    (OUT / "InvoiceIQ_Subtitles.srt").write_text("\n\n".join(
        f"{i+1}\n{stamp(a)} --> {stamp(b)}\n{line}" for i, (a, b, line) in enumerate(cues)) + "\n", encoding="utf-8")
    (OUT / "InvoiceIQ_Narration.txt").write_text("\n\n".join(
        f"{scene['title']}\n{scene['text']}" for scene in SCENES) + "\n", encoding="utf-8")
    ass = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Segoe UI,46,&H00FFFFFF,&H00FFFFFF,&H2A0F211A,&H2A0F211A,-1,0,0,0,100,100,0,0,3,11,0,2,95,95,29,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ass += "\n".join(f"Dialogue: 0,{stamp(a, True)},{stamp(b, True)},Caption,,0,0,0,,{line}"
                     for a, b, line in cues)
    (FRAMES / "captions.ass").write_text(ass + "\n", encoding="utf-8")
    score = SEGMENTS / "original-music.wav"
    music(score)
    thumbnail(marks)
    print("Burning subtitles and mixing audio", flush=True)
    ff("-f", "concat", "-safe", 0, "-i", SEGMENTS / "videos.txt",
       "-f", "concat", "-safe", 0, "-i", SEGMENTS / "voices.txt", "-i", score,
       "-filter_complex_threads", 2, "-filter_complex",
       "[0:v]ass=frames/captions.ass[v];"
       "[1:a]loudnorm=I=-17:TP=-1.5:LRA=9,aresample=48000,pan=stereo|c0=c0|c1=c0,asplit=2[voice][key];"
       "[2:a][key]sidechaincompress=threshold=0.018:ratio=4:attack=50:release=800[bed];"
       "[voice][bed]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.94[a]",
       "-map", "[v]", "-map", "[a]", "-t", TOTAL, "-c:v", "libx264", "-threads", 5,
       "-preset", "fast", "-crf", 18, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart", OUT / "InvoiceIQ_Week01_Demo.mp4")


if __name__ == "__main__":
    main()
