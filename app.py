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


# ---------------------------------
# Step placeholders manager
# ---------------------------------
def init_steps():
    steps = [
        {"name": "Extracting Topics"},
        {"name": "Building Q&A JSON"},
        {"name": "Clearing Old Outputs"},
        {"name": "Saving Q&A Files"},
        {"name": "Generating Audio (MP3s)"},
        {"name": "Creating Text ZIP"},
        {"name": "Creating Audio ZIP"},
        {"name": "Creating Combined ZIP"},
    ]
    placeholders = {}
    table = st.container()

    with table:
        cols = st.columns([2, 2, 4, 2])
        cols[0].markdown("**Step**")
        cols[1].markdown("**Status**")
        cols[2].markdown("**Progress**")
        cols[3].markdown("**Action**")

        for step in steps:
            c1, c2, c3, c4 = st.columns([2, 2, 4, 2])
            placeholders[step["name"]] = {
                "status": c2.empty(),
                "progress": c3.progress(0),
                "pct": c3.empty(),
                "btn": c4.empty(),
            }
            c1.markdown(f"**{step['name']}**")

    return steps, placeholders


def update_step(step_name, status, pct, placeholders, stop_flag, show_stop=False):
    """Update one row of the step table"""
    if status == "waiting":
        placeholders[step_name]["status"].markdown("⏳ Waiting")
    elif status == "running":
        placeholders[step_name]["status"].markdown("🔄 Running")
    elif status == "done":
        placeholders[step_name]["status"].markdown("✅ Done")

    placeholders[step_name]["progress"].progress(pct)
    placeholders[step_name]["pct"].markdown(f"{pct}%")

    if show_stop and not stop_flag.get("stop", False):
        if placeholders[step_name]["btn"].button("⏹ Stop", key=f"stop_btn_{step_name}"):
            stop_flag["stop"] = True


# ---------------------------------
# Main App
# ---------------------------------
def main():
    st.title("🤖 AI Interview Preparation")

    # Session state
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

            steps, placeholders = init_steps()
            stop_flag = {"stop": False}

            # STEP 1: Extract Topics
            step = "Extracting Topics"
            update_step(step, "running", 10, placeholders, stop_flag)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: update_step(step, "running", pct, placeholders, stop_flag),
            )
            topic_tree["topics"] = topic_tree["topics"][:1]  # limit for testing
            st.session_state.topic_tree = topic_tree
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 2: Build Q&A JSON
            step = "Building Q&A JSON"
            update_step(step, "running", 50, placeholders, stop_flag)
            _ = build_qna_json("dummy_topic", st.session_state.resume_text)  # preview run
            time.sleep(1)
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 3: Clear outputs
            step = "Clearing Old Outputs"
            update_step(step, "running", 30, placeholders, stop_flag)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            time.sleep(1)
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 4: Save QnA
            step = "Saving Q&A Files"
            update_step(step, "running", 0, placeholders, stop_flag, show_stop=True)
            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: update_step(step, "running", pct, placeholders, stop_flag, show_stop=True),
                stop_flag=stop_flag,
            )
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 5: Generate Audio
            step = "Generating Audio (MP3s)"
            update_step(step, "running", 50, placeholders, stop_flag)
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)
            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(txt_files, OUTPUT_DIR, audio_dir)
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 6: Create Text ZIP
            step = "Creating Text ZIP"
            update_step(step, "running", 50, placeholders, stop_flag)
            zip_text = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))
            st.session_state.zip_text = zip_text
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 7: Create Audio ZIP
            step = "Creating Audio ZIP"
            update_step(step, "running", 50, placeholders, stop_flag)
            zip_audio = zip_dir(audio_dir, Path("interview_qna_audio.zip"))
            st.session_state.zip_audio = zip_audio
            update_step(step, "done", 100, placeholders, stop_flag)

            # STEP 8: Create Combined ZIP
            step = "Creating Combined ZIP"
            update_step(step, "running", 50, placeholders, stop_flag)
            both_dir = OUTPUT_DIR.parent / "both_output"
            if both_dir.exists():
                shutil.rmtree(both_dir)
            both_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(zip_text, both_dir / "interview_qna_texts.zip")
            shutil.copy(zip_audio, both_dir / "interview_qna_audio.zip")
            zip_both = zip_dir(both_dir, Path("interview_qna_texts+audio.zip"))
            st.session_state.zip_both = zip_both
            update_step(step, "done", 100, placeholders, stop_flag)

            st.session_state.processing_done = True

        # Downloads
        if st.session_state.processing_done:
            st.success("✅ All questions generated!")
            c1, c2, c3 = st.columns(3)
            with c1:
                with open(st.session_state.zip_text, "rb") as f:
                    st.download_button("Download Text (ZIP)", f, file_name="interview_qna_texts.zip")
            with c2:
                with open(st.session_state.zip_audio, "rb") as f:
                    st.download_button("Download MP3 (ZIP)", f, file_name="interview_qna_audio.zip")
            with c3:
                with open(st.session_state.zip_both, "rb") as f:
                    st.download_button("Download TEXT + MP3 (ZIP)", f, file_name="interview_qna_texts+audio.zip")


if __name__ == "__main__":
    main()
