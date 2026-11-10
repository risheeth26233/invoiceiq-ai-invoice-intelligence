# Reproduce the InvoiceIQ demo

Requires Node.js, the existing frontend Playwright dependency, Microsoft Edge, Python 3.12+, Pillow, NumPy, edge-tts, FFmpeg with libass, FFprobe, and Windows Segoe UI fonts. Run the following commands from the repository root.

```powershell
npm.cmd --prefix frontend ci
node frontend/node_modules/playwright/cli.js install ffmpeg
python -m pip install Pillow numpy edge-tts
node showcase-video/production/capture.cjs
python showcase-video/production/narrate.py
python showcase-video/production/render.py
```

The capture starts with a fresh browser context and uses only the hosted Juniper Studio invoice. It temporarily saves one record and removes that record after the recording. Browser profiles, cookies, and raw captures are excluded from version control.

`scenes.json` is the editable timeline. `narrate.py` sends only the narration text to the Edge speech service and generates word timings with the en-US-AriaNeural voice. It also accepts individual scene keys for rerecording selected lines. `render.py` trims the genuine recording to its marked scenes, creates the original motion graphics and synthesized instrumental, and exports the H.264/AAC MP4, PNG thumbnail, SRT, and narration text. Remove obsolete encoded segments from the ignored `segments` directory before rerendering visuals after a source change.
