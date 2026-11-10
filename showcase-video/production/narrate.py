"""Generate one English voice take and word-boundary file per shot."""
import asyncio
import json
import sys
from pathlib import Path
import edge_tts

HERE = Path(__file__).resolve().parent
SCENES = json.loads((HERE / "scenes.json").read_text(encoding="utf-8"))
VOICE = "en-US-AriaNeural"

async def main():
    folder = HERE / "audio"
    folder.mkdir(exist_ok=True)
    for scene in SCENES:
        if len(sys.argv) > 1 and scene["key"] not in sys.argv[1:]:
            continue
        name = folder / scene["key"]
        for attempt in range(3):
            try:
                await edge_tts.Communicate(scene["text"], VOICE, rate="-2%", boundary="WordBoundary").save(
                    str(name.with_suffix(".mp3")), str(name.with_suffix(".jsonl"))
                )
                print(scene["key"], flush=True)
                break
            except (TimeoutError, edge_tts.exceptions.NoAudioReceived):
                if attempt == 2:
                    raise
                await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
