# config.py
from pathlib import Path


# --- Paths ---
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEXT_ZIP_NAME = "qna_text_bundle.zip"
AUDIO_ZIP_NAME = "qna_audio_bundle.zip"


# --- LLM model ---
GROQ_MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct" # change if desired
TEMPERATURE = 0.2
MAX_TOKENS = 1024*8


# --- Generation settings ---
# How many questions per subtopic for each style
N_LONG_Q = 10
N_SHORT_Q = 10


# Whether to also ask the LLM to propose extra subtopics if missing
ALLOW_LLM_SUBTOPIC_AUGMENT = True


# --- Text extraction ---
# Max pages to read in PDFs (None for all). Keep small for speed if needed.
PDF_MAX_PAGES = None


# --- TTS ---
TTS_VOICE = None # keep None to use system default
TTS_RATE_DELTA = 0 # e.g., +10 faster, -10 slower