# pipeline/save_outputs.py
from __future__ import annotations
from pathlib import Path
from typing import Dict
import time
from config import OUTPUT_DIR
from io_utils.file_io import safe_name, write_text
from pipeline.qna_generation import qna_to_text


def save_qna(topic: str, subtopic: str, qna: Dict) -> Path:
    """
    Save QnA content into a text file under output/<topic>/<subtopic>.txt

    Args:
        topic (str): Main topic name
        subtopic (str): Subtopic name
        qna (Dict): Dictionary containing QnA JSON structure

    Returns:
        Path: The saved file path
    """
    t_name = safe_name(topic)
    s_name = safe_name(subtopic)
    out_dir = OUTPUT_DIR / t_name
    out_path = out_dir / f"{s_name}.txt"

    content = qna_to_text(qna)
    write_text(out_path, content)
    return out_path


def save_all_qna(topic_tree: Dict, resume_text: str, qna_builder, progress_callback=None) -> None:
    """
    Save all QnA files for a given topic tree with progress updates.
    """
    subtopics = []
    for topic in topic_tree.get("topics", []):
        for sub in topic.get("subtopics", []):
            subtopics.append((topic.get("topic", "General"), sub))

    total = len(subtopics)
    for idx, (t_name, sub) in enumerate(subtopics, start=1):
        try:
            qna = qna_builder(resume_text, sub)
        except:
            continue
        save_qna(t_name, sub, qna)
        time.sleep(0.5)  # throttle if needed

        if progress_callback:
            progress_callback(int(idx / total * 100))