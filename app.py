import streamlit as st
from pathlib import Path
import tempfile
import shutil
import time

from io_utils.text_extract import extract_text_any
from pipeline.topic_extraction import get_topic_tree
from pipeline.qna_generation import build_qna_json
from pipeline.save_outputs import save_all_qna
from io_utils.zipping import zip_dir
from pipeline.tts_convert import txt_to_mp3_tree

from config import OUTPUT_DIR


# ---------------------------
# UI helpers
# ---------------------------
class StepRow:
    def __init__(self, placeholder, name):
        self.placeholder = placeholder
        self.name = name
        self.progress = 0
        self.status = "waiting"

    def update(self, status, progress=None):
        if progress is not None:
            self.progress = progress
        self.status = status
        self.render()

    def render(self):
        with self.placeholder:
            st.markdown(f"**{self.name}**")
            col1, col2 = st.columns([3, 7])
            with col1:
                if self.status == "waiting":
                    st.markdown("⏳ Waiting")
                elif self.status == "running":
                    st.markdown("🔄 Running")
                elif self.status == "done":
                    st.markdown("✅ Done")
                elif self.status == "stopped":
                    st.markdown("⏹ Stopped")
            with col2:
                st.progress(self.progress)
                st.markdown(f"{self.progress}%")


# ---------------------------
# Main App
# ---------------------------
def main():
    st.title("🤖 AI Interview Preparation")

    # --- session state ---
    if "resume_text" not in st.session_state:
        st.session_state.resume_text = None
    if "topic_tree" not in st.session_state:
        st.session_state.topic_tree = None
    if "zip_text" not in st.session_state:
        st.session_state.zip_text = None
    if "zip_audio" not in st.session_state:
        st.session_state.zip_audio = None
    if "zip_both" not in st.session_state:
        st.session_state.zip_both = None
    if "processing_done" not in st.session_state:
        st.session_state.processing_done = False
    if "stop_qna" not in st.session_state:
        st.session_state.stop_qna = False

    uploaded_file = st.file_uploader("Upload your Resume (txt/pdf/docx)", type=["txt", "pdf", "docx"])

    if uploaded_file and not st.session_state.resume_text:
        # Save uploaded file to a temp dir
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / uploaded_file.name
            with open(tmp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.resume_text = extract_text_any(tmp_path)

    if st.session_state.resume_text:
        st.subheader("Resume Extracted")
        st.text_area("Resume Text", st.session_state.resume_text, height=300)

        if st.button("Generate Questions") and not st.session_state.processing_done:
            st.info("Processing your resume… this may take a while.")

            # --- define steps ---
            steps = [
                {"name": "Extracting Topics"},
                {"name": "Clearing Old Outputs"},
                {"name": "Saving QnA Files"},
                {"name": "Creating ZIPs"},
            ]
            step_rows = [StepRow(st.container(), s["name"]) for s in steps]

            # ---------------------------
            # STEP 1: Extract topics
            # ---------------------------
            idx = 0
            step_rows[idx].update("running", 10)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: step_rows[idx].update("running", pct),
            )
            # for testing we keep only 1 topic
            topic_tree["topics"] = topic_tree["topics"][:1]
            st.session_state.topic_tree = topic_tree
            step_rows[idx].update("done", 100)

            # ---------------------------
            # STEP 2: Clear previous outputs
            # ---------------------------
            idx = 1
            step_rows[idx].update("running", 50)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            step_rows[idx].update("done", 100)

            # ---------------------------
            # STEP 3: Generate QnA (with Stop button)
            # ---------------------------
            idx = 2
            step_rows[idx].update("running", 0)

            stop_col = st.empty()
            with stop_col.container():
                if st.button("⏹ Stop QnA Generation"):
                    st.session_state.stop_qna = True

            def stop_flag():
                return st.session_state.stop_qna

            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: step_rows[idx].update("running", pct),
                stop_flag=stop_flag,
            )

            if st.session_state.stop_qna:
                step_rows[idx].update("stopped", step_rows[idx].progress)
            else:
                step_rows[idx].update("done", 100)

            stop_col.empty()  # remove stop button

            # ---------------------------
            # STEP 4: Zip results
            # ---------------------------
            idx = 3
            step_rows[idx].update("running", 30)

            # create text zip
            zip_text = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))
            st.session_state.zip_text = zip_text

            # create audio dir + zip
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)
            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(txt_files, OUTPUT_DIR, audio_dir)
            zip_audio = zip_dir(Path(audio_dir), Path("interview_qna_audio.zip"))
            st.session_state.zip_audio = zip_audio

            # create both zip
            both_dir = OUTPUT_DIR.parent / "both_output"
            if both_dir.exists():
                shutil.rmtree(both_dir)
            both_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(zip_text, both_dir / Path(zip_text).name)
            shutil.copy(zip_audio, both_dir / Path(zip_audio).name)
            zip_both = zip_dir(both_dir, Path("interview_qna_texts_and_audio.zip"))
            st.session_state.zip_both = zip_both

            step_rows[idx].update("done", 100)

            # mark pipeline done
            st.session_state.processing_done = True

        # ---------------------------
        # Show download buttons
        # ---------------------------
        if st.session_state.processing_done:
            st.success("✅ All questions generated!")
            with open(st.session_state.zip_text, "rb") as f:
                st.download_button("⬇️ Download Text (ZIP)", f, file_name="interview_qna_texts.zip")
            with open(st.session_state.zip_audio, "rb") as f:
                st.download_button("🎧 Download Audio (ZIP)", f, file_name="interview_qna_audio.zip")
            with open(st.session_state.zip_both, "rb") as f:
                st.download_button("📦 Download TEXT + MP3 (ZIP)", f, file_name="interview_qna_texts_and_audio.zip")


if __name__ == "__main__":
    main()
