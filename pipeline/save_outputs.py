# pipeline/save_outputs.py
from __future__ import annotations
from pathlib import Path
from typing import Dict
import time
import json
from config import OUTPUT_DIR
from io_utils.file_io import safe_name, write_text
from pipeline.qna_generation import qna_to_text
from typing import Dict, Callable, Optional, Any

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


def save_all_qna(
    topic_tree: Dict,
    resume_text: str,
    qna_builder: Callable,
    progress_callback: Callable[[int], None] | None = None,
    stop_flag: Callable[[], bool] | None = None,
) -> None:
    """
    Save all QnA files for a given topic tree.

    Args:
        topic_tree (Dict): The topic → subtopics JSON
        resume_text (str): Resume text context
        qna_builder (Callable): Function that builds QnA JSON from (resume_text, unit_name)
        progress_callback (Callable, optional): Function to update progress %
        stop_flag (Callable, optional): Function returning True if process should stop
    """
    topics = topic_tree.get("topics", [])
    total_subs = sum(len(t.get("subtopics", [])) for t in topics)
    done = 0

    for topic in topics:
        t_name = topic.get("topic", "General")
        for sub in topic.get("subtopics", []):
            if stop_flag and stop_flag():  # Stop requested
                return

            qna = qna_builder(resume_text, sub)
            save_qna(t_name, sub, qna)

            done += 1
            if progress_callback:
                pct = int(done / total_subs * 100)
                progress_callback(pct)

            time.sleep(0.5)  # Throttle