from __future__ import annotations
import json
from typing import Dict


from config import N_LONG_Q, N_SHORT_Q
from core.llm_client import run_prompt, parse_json_safely
from core.prompts import QNA_PROMPT_TEMPLATE




def build_qna_json(resume_text: str, unit_name: str) -> Dict:
    print(f"unit_name:{unit_name}\nn_long:{N_LONG_Q}\nn_short:{N_SHORT_Q}")
    prompt = QNA_PROMPT_TEMPLATE.format(
                                        unit_name=unit_name,
                                        n_long=N_LONG_Q,
                                        n_short=N_SHORT_Q,
                                        )
    print("Prompt is ready......")
    user = f"Resume/Profile Context:\n{resume_text}\n\nTask: Create questions for: {unit_name}"
    raw = run_prompt("You generate interview QnA.", prompt + "\n\n" + user)
    for retry in range(5):
        try:
            data = parse_json_safely(raw)
            break
        except:
            raw = run_prompt("You generate interview QnA.", prompt + "\n\n" + user)
            print(f"Retry No : {retry}")
            continue


    # Minimal schema guardrails
    data.setdefault("unit", unit_name)
    data.setdefault("long", [])
    data.setdefault("short", [])
    return data




def qna_to_text(qna: Dict) -> str:
    lines = [f"Unit: {qna.get('unit', '')}", "", "LONG-ANSWER:"]
    for i, item in enumerate(qna.get("long", []), 1):
        lines.append(f"{i}. Q: {item.get('q','')}")
        lines.append(f" A: {item.get('a','')}")
        lines.append("")
    lines.append("SHORT-ANSWER:")
    for i, item in enumerate(qna.get("short", []), 1):
        lines.append(f"{i}. Q: {item.get('q','')}")
        lines.append(f" A: {item.get('a','')}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"