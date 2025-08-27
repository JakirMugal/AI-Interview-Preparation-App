# pipeline/tts_convert.py
from __future__ import annotations
from pathlib import Path
from typing import Iterable


from io_utils.file_io import read_text

from gtts import gTTS

def txt_to_mp3_tree(
    txt_files: Iterable[Path],
    base_dir: Path,
    out_audio_root: Path,
    lang: str = 'en',
    progress_callback=None
) -> None:
    txt_files = list(txt_files)
    total = len(txt_files)

    for idx, txt_path in enumerate(txt_files, start=1):
        rel_path = txt_path.relative_to(base_dir)
        mp3_path = out_audio_root / rel_path.with_suffix(".mp3")
        mp3_path.parent.mkdir(parents=True, exist_ok=True)

        content = read_text(txt_path)
        tts = gTTS(text=content, lang=lang)
        tts.save(str(mp3_path))

        if progress_callback:
            progress_callback(int(idx / total * 100))
