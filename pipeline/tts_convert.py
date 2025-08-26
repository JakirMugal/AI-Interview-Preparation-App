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
    rate_delta: int = 0
) -> None:
    """
    Convert all .txt files to .mp3 files mirroring the same folder structure.

    Args:
        txt_files (Iterable[Path]): List of text file paths
        base_dir (Path): Base directory of original text files
        out_audio_root (Path): Root folder for generated mp3 files
        voice (str, optional): Voice id to use (default: system default)
        rate_delta (int, optional): Adjust speaking rate (+/-)
    """
    engine = pyttsx3.init()

    # Apply optional config
    if rate_delta:
        rate = engine.getProperty("rate")
        engine.setProperty("rate", rate + rate_delta)
    if voice:
        engine.setProperty("voice", voice)

    for txt_path in txt_files:
        rel_path = txt_path.relative_to(base_dir)
        mp3_path = out_audio_root / rel_path.with_suffix(".mp3")
        mp3_path.parent.mkdir(parents=True, exist_ok=True)

        content = read_text(txt_path)
        engine.save_to_file(content, str(mp3_path))

    # Process queued saves
    engine.runAndWait()
