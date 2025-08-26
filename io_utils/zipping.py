from __future__ import annotations
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED




def zip_dir(dir_path: Path, zip_path: Path) -> Path:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as zf:
        for p in dir_path.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(dir_path))
    return zip_path