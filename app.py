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
# UI: Step Table
# ---------------------------
def init_step_table():
    """Initialize placeholders for steps table (only once)."""
    if "step_placeholders" not in st.session_state:
        st.session_state.step_placeholders = {}

        steps = ["Extracting Topics", "Clearing Old Outputs", "Saving QnA Files", "Creating ZIPs"]
        for step in steps:
            container = st.container()
            col1, col2, col3, col4, col5 = container.columns([2, 2, 4, 1, 2])
            with col1: st.markdown(f"**{step}**")
            with col2: status = st.empty()
            with col3: bar = st.progress(0)
            with col4: pct = st.empty()
            with col5: btn = st.empty()
            st.session_state.step_placeholders[step] = {
                "status": status,
                "bar": bar,
                "pct": pct,
                "btn": btn,
            }


def update_step(step, status, progress, show_stop=False):
    """Update row for a step."""
    placeholders = st.session_state.step_placeholders[step]

    # status text
    if status == "waiting":
        placeholders["status"].markdown("⏳ Waiting")
    elif status == "running":
        placeholders["status"].markdown("🔄 Running")
    elif status == "done":
        placeholders["status"].markdown("✅ Done")
    elif status == "stopped":
        placeholders["status"].markdown("⏹ Stopped")

    # progress
    placeholders["bar"].progress(progress)
    placeholders["pct"].markdown(f"{progress}%")

    # stop button only for QnA
    if show_stop and status == "running":
        if placeholders["btn"].button("⏹ Stop", key="stop_btn"):
            st.session_state.stop_qna = True
    else:
        placeholders["btn"].empty()


# ---------------------------
# Main
# ---------------------------
def main():
    st.title("🤖 AI Interview Preparation")

    # Initialize state
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

            # init fixed table
            init_step_table()

            # ---------------------------
            # STEP 1: Extract topics
            # ---------------------------
            update_step("Extracting Topics", "running", 0)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: update_step("Extracting Topics", "running", pct),
            )
            topic_tree["topics"] = topic_tree["topics"][:1]  # sample topics
            st.session_state.topic_tree = topic_tree
            update_step("Extracting Topics", "done", 100)

            # ---------------------------
            # STEP 2: Clear outputs
            # ---------------------------
            update_step("Clearing Old Outputs", "running", 50)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            update_step("Clearing Old Outputs", "done", 100)

            # ---------------------------
            # STEP 3: Generate QnA
            # ---------------------------
            update_step("Saving QnA Files", "running", 0, show_stop=True)

            def stop_flag():
                return st.session_state.stop_qna

            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: update_step(
                    "Saving QnA Files",
                    "running" if not st.session_state.stop_qna else "stopped",
                    pct,
                    show_stop=True,
                ),
                stop_flag=stop_flag,
            )

            if st.session_state.stop_qna:
                update_step("Saving QnA Files", "stopped", 100)
            else:
                update_step("Saving QnA Files", "done", 100)

            # ---------------------------
            # STEP 4: Zip results
            # ---------------------------
            update_step("Creating ZIPs", "running", 30)

            # text zip
            zip_text = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))
            st.session_state.zip_text = zip_text

            # audio zip
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)
            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(txt_files, OUTPUT_DIR, audio_dir)
            zip_audio = zip_dir(Path(audio_dir), Path("interview_qna_audio.zip"))
            st.session_state.zip_audio = zip_audio

            # both zip
            both_dir = OUTPUT_DIR.parent / "both_output"
            if both_dir.exists():
                shutil.rmtree(both_dir)
            both_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(zip_text, both_dir / Path(zip_text).name)
            shutil.copy(zip_audio, both_dir / Path(zip_audio).name)
            zip_both = zip_dir(both_dir, Path("interview_qna_texts_and_audio.zip"))
            st.session_state.zip_both = zip_both

            update_step("Creating ZIPs", "done", 100)

            st.session_state.processing_done = True

        # ---------------------------
        # Downloads
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
