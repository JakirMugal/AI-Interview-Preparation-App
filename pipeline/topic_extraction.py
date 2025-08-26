from __future__ import annotations
from typing import Dict, List


from core.llm_client import run_prompt, parse_json_safely
from core.prompts import TOPIC_TREE_PROMPT
from core.splitter import chunk_text




def get_topic_tree(resume_text: str) -> Dict:
    # If resume is long, run multi-chunk and let model merge implicitly
    chunks = chunk_text(resume_text)
    merged_topics: Dict[str, List[str]] = {}


    for idx, ch in enumerate(chunks):
        user = TOPIC_TREE_PROMPT + "\n\nResume chunk (part %d/%d):\n" % (idx+1, len(chunks)) + ch
        raw = run_prompt("You structure topics.", user)
        data = parse_json_safely(raw)
        for t in data.get("topics", []):
            topic = t.get("topic", "General").strip()
            subs = [s.strip() for s in t.get("subtopics", []) if isinstance(s, str)]
            merged_topics.setdefault(topic, [])
            for s in subs:
                if s not in merged_topics[topic]:
                    merged_topics[topic].append(s)


    # Convert map -> list schema
    return {
    "topics": [
    {"topic": k, "subtopics": v} for k, v in merged_topics.items()
    ]
}