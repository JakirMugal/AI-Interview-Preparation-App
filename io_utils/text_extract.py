from __future__ import annotations
from pathlib import Path
from typing import Optional


from config import PDF_MAX_PAGES




def extract_text_any(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in {".docx"}:
        return _extract_docx(path)
    # Fallback: try reading as text
    return path.read_text(encoding="utf-8", errors="ignore")




def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    text_parts = []
    max_pages = PDF_MAX_PAGES or len(reader.pages)
    for i in range(min(len(reader.pages), max_pages)):
        text_parts.append(reader.pages[i].extract_text() or "")
    return "\n".join(text_parts)




def _extract_docx(path: Path) -> str:
    import docx
    doc = docx.Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs)