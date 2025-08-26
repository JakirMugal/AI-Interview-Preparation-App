import json
import os
from typing import Any, Dict


from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os

load_dotenv()  # loads variables from .env

from config import GROQ_MODEL_NAME, TEMPERATURE, MAX_TOKENS




def get_client() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in environment.")
    return ChatGroq(model=GROQ_MODEL_NAME, temperature=TEMPERATURE, max_tokens=MAX_TOKENS)




def run_prompt(system_prompt: str, user_prompt: str) -> str:
    llm = get_client()
    messages = [
    SystemMessage(content=system_prompt.strip()),
    HumanMessage(content=user_prompt.strip()),
    ]
    resp = llm.invoke(messages)
    return resp.content




def parse_json_safely(text: str) -> Dict[str, Any]:
    """Attempt to extract JSON from the LLM output robustly."""
    try:
      return json.loads(text)
    except json.JSONDecodeError:
        # Fallback: try to find the first/last braces
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            sub = text[start:end+1]
            return json.loads(sub)