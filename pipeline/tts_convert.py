# pipeline/tts_convert.py
from __future__ import annotations
from pathlib import Path
from typing import Iterable

import pyttsx3

from io_utils.file_io import read_text


def txt_to_mp3_tree(
    txt_files: Iterable[Path],
    base_dir: Path,
    out_audio_root: Path,
    voice: str | None = None,
    rate_delta: int = 0,
    progress_callback=None
) -> None:
    """
    Convert all .txt files to .mp3 files mirroring the same folder structure.
    """
    engine = pyttsx3.init()

    # Apply optional config
    if rate_delta:
        rate = engine.getProperty("rate")
        engine.setProperty("rate", rate + rate_delta)
    if voice:
        engine.setProperty("voice", voice)

    txt_files = list(txt_files)
    total = len(txt_files)

    for idx, txt_path in enumerate(txt_files, start=1):
        rel_path = txt_path.relative_to(base_dir)
        mp3_path = out_audio_root / rel_path.with_suffix(".mp3")
        mp3_path.parent.mkdir(parents=True, exist_ok=True)

        content = read_text(txt_path)
        engine.save_to_file(content, str(mp3_path))

        # Report progress after queueing
        if progress_callback:
            progress_callback(int(idx / total * 100))

    # Process queued saves
    engine.runAndWait()
