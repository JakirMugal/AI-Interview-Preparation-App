import json
import os
from typing import Any, Dict
import streamlit as st
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env

from config import TEMPERATURE, MAX_TOKENS

# Top ~10 useful models for this project (ordered by preference)
CANDIDATE_MODELS = [
    "gemma2-9b-it",
    "llama-3.1-8b-instant",
    "llama3-8b-8192",
    "llama3-70b-8192",
    "llama-3.3-70b-versatile",
    "allam-2-7b",
    "qwen/qwen3-32b",
    "deepseek-r1-distill-llama-70b",
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
]


class DynamicLLMClient:
    def __init__(self, api_key: str = None, temperature: float = TEMPERATURE, max_tokens: int = MAX_TOKENS):
        self.api_key = api_key or st.secrets["GROQ_API_KEY"]
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not set in environment.")

        self.temperature = temperature
        self.max_tokens = max_tokens
        self.models = CANDIDATE_MODELS
        self.current_index = 0  # start with first model

    def _get_client(self, model_name: str) -> ChatGroq:
        return ChatGroq(
            model=model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def run_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Try multiple models dynamically until success."""
        last_error = None
        for _ in range(len(self.models)):
            model_name = self.models[self.current_index]
            try:
                print(f"[INFO] Using model: {model_name}")
                llm = self._get_client(model_name)
                messages = [
                    SystemMessage(content=system_prompt.strip()),
                    HumanMessage(content=user_prompt.strip()),
                ]
                resp = llm.invoke(messages)
                return resp.content  # success
            except Exception as e:
                print(f"[WARN] Model {model_name} failed: {e}")
                last_error = e
                self.current_index = (self.current_index + 1) % len(self.models)

        raise RuntimeError(f"All models failed. Last error: {last_error}")


def parse_json_safely(text: str) -> Dict[str, Any]:
    """Attempt to extract JSON from the LLM output robustly."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            sub = text[start:end+1]
            return json.loads(sub)
        raise


# Singleton client for easy importing
llm_client = DynamicLLMClient()
