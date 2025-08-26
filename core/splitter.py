from typing import List




def chunk_text(text: str, max_chars: int = 12000) -> List[str]:
    """Lightweight text chunker by character length to keep prompts manageable."""
    text = text or ""
    if len(text) <= max_chars:
        return [text]
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i:i+max_chars])
        i += max_chars
    return chunks