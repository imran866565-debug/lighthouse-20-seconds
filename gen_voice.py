#!/usr/bin/env python3
"""Generate the male voiceover for the Lighthouse short with edge-tts.

NOTE: aiohttp in this sandbox does NOT pick up the proxy env vars, so the
proxy must be passed explicitly to Communicate (see ~/TOOLS.md).
"""
import asyncio
import os
import sys

import edge_tts

VOICE = "en-US-GuyNeural"  # male voice


async def main():
    beats = [line.strip() for line in open("beats.txt", encoding="utf-8") if line.strip()]
    text = " ".join(beats)
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    communicate = edge_tts.Communicate(text, VOICE, proxy=proxy)
    await communicate.save("voice.mp3")
    print(f"saved voice.mp3 ({len(beats)} beats, {len(text.split())} words, voice {VOICE})")


if __name__ == "__main__":
    asyncio.run(main())
