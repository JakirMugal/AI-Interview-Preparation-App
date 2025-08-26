from __future__ import annotations
import re
from pathlib import Path


SAFE = re.compile(r"[^\w\- ]+")




def safe_name(name: str) -> str:
    name = name.strip().replace("/", "-")
    name = SAFE.sub("_", name)
    return name[:120] or "unit"




def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")




def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")