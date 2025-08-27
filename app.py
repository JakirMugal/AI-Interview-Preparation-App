import streamlit as st
from pathlib import Path
import tempfile
import shutil

from io_utils.text_extract import extract_text_any
from pipeline.topic_extraction import get_topic_tree
from pipeline.qna_generation import build_qna_json
from pipeline.save_outputs import save_all_qna
from io_utils.zipping import zip_dir
from pipeline.tts_convert import txt_to_mp3_tree

from config import OUTPUT_DIR


def main():
    st.title("🤖 AI Interview Preparation")

    uploaded_file = st.file_uploader(
        "Upload your Resume (txt/pdf/docx)", type=["txt", "pdf", "docx"]
    )

    if uploaded_file:
        # Save uploaded file to a temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / uploaded_file.name
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            resume_text = extract_text_any(tmp_path)

        # Store resume text in session state so it persists
        st.session_state["resume_text"] = resume_text

        st.subheader("Resume Extracted")
        st.text_area("Resume Text", resume_text, height=300)

    # --- Generate Questions ---
    if st.button("Generate Questions"):
        if "resume_text" not in st.session_state:
            st.error("Please upload a resume first.")
            return

        resume_text = st.session_state["resume_text"]

        st.info("Extracting topics and generating questions… this may take a while.")

        # 1. Extract topics
        topic_tree = get_topic_tree(resume_text)

        # 2. Clear previous outputs
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        # 3. Generate QnA files
        save_all_qna(topic_tree, resume_text, build_qna_json)

        # 4. Zip results
        zip_path = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))

        # Save path to session state
        st.session_state["zip_path"] = zip_path
        st.success("✅ All questions generated!")

    # --- Download QnA ZIP ---
    if "zip_path" in st.session_state:
        with open(st.session_state["zip_path"], "rb") as f:
            st.download_button(
                "Download QnA (ZIP)", f, file_name="interview_qna_texts.zip"
            )

        # --- Convert to MP3 ---
        if st.button("Convert to MP3"):
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)

            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(txt_files, OUTPUT_DIR, audio_dir)

            zip_audio = zip_dir(audio_dir, "interview_qna_audio.zip")
            st.session_state["zip_audio"] = zip_audio
            st.success("🎵 Audio conversion complete!")

    # --- Download Audio ZIP ---
    if "zip_audio" in st.session_state:
        with open(st.session_state["zip_audio"], "rb") as f:
            st.download_button(
                "Download Audio (ZIP)", f, file_name="interview_qna_audio.zip"
            )


if __name__ == "__main__":
    main()
