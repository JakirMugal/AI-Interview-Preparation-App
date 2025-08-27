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


# ---------------------------
# Step Row Manager
# ---------------------------
class StepRow:
    def __init__(self, container, name):
        self.name = name
        col1, col2, col3 = container.columns([2, 2, 6])
        with col1:
            st.markdown(f"**{name}**")
        self.status_placeholder = col2.empty()
        self.progress_placeholder = col3.progress(0)
        self.percent_placeholder = col3.empty()

    def update(self, status, progress):
        if status == "waiting":
            self.status_placeholder.markdown("⏳ Waiting")
        elif status == "running":
            self.status_placeholder.markdown("🔄 Running")
        elif status == "done":
            self.status_placeholder.markdown("✅ Done")
        self.progress_placeholder.progress(progress)
        self.percent_placeholder.markdown(f"{progress}%")


def main():
    st.title("🤖 AI Interview Preparation")

    # ---------------------------
    # Session state initialization
    # ---------------------------
    for key in ["resume_text", "topic_tree", "zip_text", "zip_audio", "zip_both", "processing_done"]:
        if key not in st.session_state:
            st.session_state[key] = None if key != "processing_done" else False

    uploaded_file = st.file_uploader("Upload your Resume (txt/pdf/docx)", type=["txt", "pdf", "docx"])

    if uploaded_file and not st.session_state.resume_text:
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

            steps = [
                "Extracting Topics",
                "Clearing Old Outputs",
                "Saving QnA Files",
                "Creating Text ZIP",
                "Converting to MP3",
                "Creating Audio ZIP",
                "Packaging TEXT + MP3",
            ]

            # One StepRow per step
            step_rows = [StepRow(st.container(), step) for step in steps]

            # Initialize all as waiting
            for row in step_rows:
                row.update("waiting", 0)

            # ---------------------------
            # STEP 1: Extract Topics
            # ---------------------------
            idx = 0
            step_rows[idx].update("running", 0)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: step_rows[idx].update("running", pct),
            )
            step_rows[idx].update("done", 100)
            st.session_state.topic_tree = topic_tree

            # STEP 2: Clear outputs
            idx = 1
            step_rows[idx].update("running", 50)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            step_rows[idx].update("done", 100)

            # STEP 3: Generate QnA
            idx = 2
            step_rows[idx].update("running", 0)
            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: step_rows[idx].update("running", pct),
            )
            step_rows[idx].update("done", 100)

            # STEP 4: Create Text ZIP
            idx = 3
            step_rows[idx].update("running", 50)
            zip_text = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))
            step_rows[idx].update("done", 100)
            st.session_state.zip_text = zip_text

            # STEP 5: Convert to MP3
            idx = 4
            step_rows[idx].update("running", 0)
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)
            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(
                txt_files,
                OUTPUT_DIR,
                audio_dir,
                progress_callback=lambda pct: step_rows[idx].update("running", pct),
            )
            step_rows[idx].update("done", 100)

            # STEP 6: Audio ZIP
            idx = 5
            step_rows[idx].update("running", 50)
            zip_audio = zip_dir(Path(audio_dir), Path("interview_qna_audio.zip"))
            step_rows[idx].update("done", 100)
            st.session_state.zip_audio = zip_audio

            # STEP 7: Package TEXT + MP3
            idx = 6
            step_rows[idx].update("running", 50)
            combined_dir = OUTPUT_DIR.parent / "combined_output"
            if combined_dir.exists():
                shutil.rmtree(combined_dir)
            combined_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(OUTPUT_DIR, combined_dir / "texts")
            shutil.copytree(audio_dir, combined_dir / "audio")
            zip_both = zip_dir(combined_dir, Path("interview_qna_texts_and_audio.zip"))
            step_rows[idx].update("done", 100)
            st.session_state.zip_both = zip_both

            st.session_state.processing_done = True

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
