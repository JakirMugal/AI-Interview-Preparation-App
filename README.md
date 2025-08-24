# AI Interview Preparation App (Streamlit + LangChain/Groq)

A modular Streamlit app that:

1. Lets a user upload a resume/profile text (TXT/PDF/DOCX)
2. Extracts all possible topics and subtopics using an LLM (Groq via LangChain)
3. Iterates through each (topic → subtopic) and generates two types of questions:

   * **Long-answer** (answers \~5–6 lines)
   * **Short-answer** (answers \~1–3 lines)
4. Saves each subtopic’s Q\&A to `output/<topic>/<subtopic>.txt`
5. Zips all text files for download
6. Optional: Converts all TXT files to MP3 with offline TTS and zips again

---

## Project Structure

```
ai-interview-prep/
├─ app.py
├─ README.md
├─ requirements.txt
├─ config.py
├─ core/
│  ├─ prompts.py
│  ├─ llm_client.py
│  └─ splitter.py
├─ io_utils/
│  ├─ file_io.py
│  ├─ text_extract.py
│  └─ zipping.py
├─ pipeline/
│  ├─ topic_extraction.py
│  ├─ qna_generation.py
│  ├─ save_outputs.py
│  └─ tts_convert.py
└─ output/               # created at runtime
```

---

## Setup

1. **Python version:** 3.10+ recommended (Windows supported)
2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```
3. **Environment variable:**

   * Set your Groq key

     * PowerShell: `setx GROQ_API_KEY "<your_key>"`
     * Linux/macOS: `export GROQ_API_KEY="<your_key>"`
4. **Run app:**

   ```bash
   streamlit run app.py
   ```
