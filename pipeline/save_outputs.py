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


def save_all_qna(topic_tree, resume_text, qna_builder, progress_callback=None, stop_flag=None) -> None:
    """
    Save all QnA files for a given topic tree.

    Args:
        topic_tree (Dict): The topic → subtopics JSON
        resume_text (str): Resume text context
        qna_builder (Callable): Function that builds QnA JSON from (resume_text, unit_name)
        progress_callback (Callable, optional): Function to report progress percentage
        stop_flag (Callable, optional): Function that returns True if the process should stop
    """
    topics = topic_tree.get("topics", [])
    total_subs = sum(len(t.get("subtopics", [])) for t in topics)
    done = 0

    for topic in topics:
        t_name = topic.get("topic", "General")

        for sub in topic.get("subtopics", []):
            # --- check stop flag ---
            if stop_flag and stop_flag():
                print("⏹ QnA generation stopped by user")
                return  # exit early, keep already generated files

            # --- generate QnA ---
            try:
                qna = qna_builder(resume_text, sub)
                save_qna(t_name, sub, qna)
            except Exception as e:
                print(f"⚠️ Failed to build QnA for {t_name} → {sub}: {e}")

            # --- update progress ---
            done += 1
            pct = int((done / total_subs) * 100)
            if progress_callback:
                progress_callback(pct)

            time.sleep(0.5)  # small delay to simulate work / avoid overload