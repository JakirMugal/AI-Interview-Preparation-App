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


def save_all_qna(topic_tree, resume_text, build_qna_json, progress_callback=None, stop_flag=None):
    """
    Save QnA JSONs into files, one folder per topic.
    
    Args:
        topic_tree (dict): Tree of extracted topics.
        resume_text (str): Extracted resume text.
        build_qna_json (function): Function to generate QnA for a topic.
        progress_callback (callable): Called with percentage progress.
        stop_flag (dict): {"stop": bool} flag to support early stopping.
    """
    topics = topic_tree.get("topics", [])
    total = len(topics)

    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, topic in enumerate(topics):
        # ✅ Stop button pressed
        if stop_flag and stop_flag.get("stop", False):
            print("⏹️ Stopping QnA generation early...")
            break

        # Generate QnA JSON for topic
        qna_json = build_qna_json(topic, resume_text)

        # Create topic folder
        topic_dir = OUTPUT_DIR / topic["title"].replace(" ", "_")
        topic_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON file
        json_path = topic_dir / "qna.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(qna_json, f, indent=2, ensure_ascii=False)

        # Save TXT file (QnA in text format)
        txt_path = topic_dir / "qna.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for qna in qna_json.get("qna", []):
                f.write(f"Q: {qna['question']}\n")
                f.write(f"A: {qna['answer']}\n\n")

        # ✅ Update progress
        pct = int(((i + 1) / total) * 100)
        if progress_callback:
            progress_callback(pct)

    # If finished fully, ensure 100%
    if progress_callback and not (stop_flag and stop_flag.get("stop", False)):
        progress_callback(100)