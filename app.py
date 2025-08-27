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
# Helper UI function
# ---------------------------
def render_step(container, name, status, progress, show_stop=False):
    """Render one step row with progress bar + percentage + emoji + optional Stop button"""
    with container:
        col1, col2, col3, col4 = st.columns([2, 2, 5, 2])
        with col1:
            st.markdown(f"**{name}**")
        with col2:
            if status == "waiting":
                st.markdown("⏳ Waiting")
            elif status == "running":
                st.markdown("🔄 Running")
            elif status == "done":
                st.markdown("✅ Done")
            elif status == "stopped":
                st.markdown("⏹ Stopped")
        with col3:
            st.progress(progress)
        with col4:
            if show_stop and status == "running":
                if st.button("⏹ Stop", key="stop_btn"):
                    st.session_state.stop_qna = True


def main():
    st.title("🤖 AI Interview Preparation")

    # Initialize session state
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

            # Step placeholders
            step_placeholders = [st.container() for _ in range(4)]

            # ---------------------------
            # STEP 1: Extract topics
            # ---------------------------
            render_step(step_placeholders[0], "Extracting Topics", "running", 0)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: render_step(step_placeholders[0], "Extracting Topics", "running", pct),
            )
            topic_tree["topics"] = topic_tree["topics"][:1]  # test with 1 topic
            st.session_state.topic_tree = topic_tree
            render_step(step_placeholders[0], "Extracting Topics", "done", 100)

            # ---------------------------
            # STEP 2: Clear previous outputs
            # ---------------------------
            render_step(step_placeholders[1], "Clearing Old Outputs", "running", 50)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            render_step(step_placeholders[1], "Clearing Old Outputs", "done", 100)

            # ---------------------------
            # STEP 3: Generate QnA (with Stop button)
            # ---------------------------
            render_step(step_placeholders[2], "Saving QnA Files", "running", 0, show_stop=True)

            def stop_flag():
                return st.session_state.stop_qna

            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: render_step(
                    step_placeholders[2],
                    "Saving QnA Files",
                    "running" if not st.session_state.stop_qna else "stopped",
                    pct,
                    show_stop=True,
                ),
                stop_flag=stop_flag,
            )

            if st.session_state.stop_qna:
                render_step(step_placeholders[2], "Saving QnA Files", "stopped", 100)
            else:
                render_step(step_placeholders[2], "Saving QnA Files", "done", 100)

            # ---------------------------
            # STEP 4: Zip results
            # ---------------------------
            render_step(step_placeholders[3], "Creating ZIPs", "running", 30)

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

            render_step(step_placeholders[3], "Creating ZIPs", "done", 100)

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
