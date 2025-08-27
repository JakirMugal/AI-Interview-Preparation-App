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

# ------------------------------
# Helper: Create limited topic tree
# ------------------------------
def create_test_topic_tree(original_tree, max_topics=2, max_subtopics=2):
    test_tree = {'topics': []}
    limited_topics = original_tree.get('topics', [])[:max_topics]
    for topic_entry in limited_topics:
        topic = topic_entry.get('topic')
        subtopics = topic_entry.get('subtopics', [])[:max_subtopics]
        test_tree['topics'].append({'topic': topic, 'subtopics': subtopics})
    return test_tree

# ------------------------------
# Step Manager
# ------------------------------
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

def update_step(step_name, status, pct, placeholders):
    if status == "waiting":
        placeholders[step_name]["status"].markdown("⏳ Waiting")
    elif status == "running":
        placeholders[step_name]["status"].markdown("🔄 Running")
    elif status == "done":
        placeholders[step_name]["status"].markdown("✅ Done")

    placeholders[step_name]["progress"].progress(pct)
    placeholders[step_name]["pct"].markdown(f"{pct}%")

# ------------------------------
# Main App
# ------------------------------
def main():
    st.title("🤖 AI Interview Preparation")

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

        col1, col2 = st.columns(2)
        with col1:
            test_button = st.button("🧪 Test with Some Topics")
        with col2:
            full_button = st.button("📚 Create Full Questions")

        if (test_button or full_button) and not st.session_state.processing_done:
            st.info("Processing your resume… this may take a while.")
            steps, placeholders = init_steps()

            # STEP 1: Extract Topics
            step = "Extracting Topics"
            update_step(step, "running", 10, placeholders)
            topic_tree = get_topic_tree(
                st.session_state.resume_text,
                progress_callback=lambda pct: update_step(step, "running", pct, placeholders),
            )
            update_step(step, "done", 100, placeholders)

            # Limit for test mode
            if test_button:
                topic_tree = create_test_topic_tree(topic_tree, max_topics=2, max_subtopics=2)

            st.session_state.topic_tree = topic_tree

            # STEP 2: Build Q&A JSON
            step = "Building Q&A JSON"
            update_step(step, "running", 50, placeholders)
            _ = build_qna_json("dummy_topic", st.session_state.resume_text)  # preview run
            time.sleep(1)
            update_step(step, "done", 100, placeholders)

            # STEP 3: Clear outputs
            step = "Clearing Old Outputs"
            update_step(step, "running", 30, placeholders)
            if OUTPUT_DIR.exists():
                shutil.rmtree(OUTPUT_DIR)
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            time.sleep(1)
            update_step(step, "done", 100, placeholders)

            # STEP 4: Save Q&A Files
            step = "Saving Q&A Files"
            update_step(step, "running", 0, placeholders)
            save_all_qna(
                topic_tree,
                st.session_state.resume_text,
                build_qna_json,
                progress_callback=lambda pct: update_step(step, "running", pct, placeholders),
            )
            update_step(step, "done", 100, placeholders)

            # STEP 5: Generate Audio (MP3s)
            step = "Generating Audio (MP3s)"
            update_step(step, "running", 50, placeholders)
            audio_dir = OUTPUT_DIR.parent / "audio_output"
            if audio_dir.exists():
                shutil.rmtree(audio_dir)
            audio_dir.mkdir(parents=True, exist_ok=True)
            txt_files = list(OUTPUT_DIR.rglob("*.txt"))
            txt_to_mp3_tree(txt_files, OUTPUT_DIR, audio_dir)
            update_step(step, "done", 100, placeholders)

            # STEP 6: Create Text ZIP
            step = "Creating Text ZIP"
            update_step(step, "running", 50, placeholders)
            zip_text = zip_dir(Path(OUTPUT_DIR), Path("interview_qna_texts.zip"))
            st.session_state.zip_text = zip_text
            update_step(step, "done", 100, placeholders)

            # STEP 7: Create Audio ZIP
            step = "Creating Audio ZIP"
            update_step(step, "running", 50, placeholders)
            zip_audio = zip_dir(audio_dir, Path("interview_qna_audio.zip"))
            st.session_state.zip_audio = zip_audio
            update_step(step, "done", 100, placeholders)

            # STEP 8: Create Combined ZIP
            step = "Creating Combined ZIP"
            update_step(step, "running", 50, placeholders)
            both_dir = OUTPUT_DIR.parent / "both_output"
            if both_dir.exists():
                shutil.rmtree(both_dir)
            both_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(zip_text, both_dir / "interview_qna_texts.zip")
            shutil.copy(zip_audio, both_dir / "interview_qna_audio.zip")
            zip_both = zip_dir(both_dir, Path("interview_qna_texts+audio.zip"))
            st.session_state.zip_both = zip_both
            update_step(step, "done", 100, placeholders)

            st.session_state.processing_done = True

        # ----------------------------
        # Download buttons
        # ----------------------------
        if st.session_state.processing_done:
            st.success("✅ All questions generated!")
            c1, c2, c3 = st.columns(3)
            with c1:
                with open(st.session_state.zip_text, "rb") as f:
                    st.download_button("📥 Download Text (ZIP)", f, file_name="interview_qna_texts.zip")
            with c2:
                with open(st.session_state.zip_audio, "rb") as f:
                    st.download_button("📥 Download MP3 (ZIP)", f, file_name="interview_qna_audio.zip")
            with c3:
                with open(st.session_state.zip_both, "rb") as f:
                    st.download_button("📥 Download TEXT + MP3 (ZIP)", f, file_name="interview_qna_texts+audio.zip")

if __name__ == "__main__":
    main()
