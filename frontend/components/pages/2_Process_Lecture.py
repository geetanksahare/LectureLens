"""
2_Process_Lecture.py
---------------------------------------------------------
Full pipeline page: upload -> extract audio -> transcribe ->
summarize -> quiz -> save everything to the database under
the logged-in user.
"""

import os
import sys
import tempfile

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.audio_extraction.audio_extractor import extract_audio
from backend.transcription.transcriber import process_audio
from backend.subtitle_generation.subtitle_generator import save_subtitles
from backend.summarization.summarizer import chunk_transcript, summarize_technical, simplify_eli_junior
from backend.quiz_generation.quiz_generator import generate_mcqs, get_weak_areas
from backend.database.db_manager import create_lecture, add_transcript_segments, save_quiz_result
from components.sidebar import render_sidebar, require_login
from components.transcript_view import render_transcript

TOTAL_MCQS = 10

st.set_page_config(page_title="Process Lecture - LectureLens", page_icon="🎬", layout="wide")

require_login()
render_sidebar()

st.title("🎬 Process a New Lecture")


def distribute_mcq_counts(num_chunks, total=TOTAL_MCQS):
    base = total // num_chunks
    remainder = total % num_chunks
    counts = [base] * num_chunks
    for i in range(remainder):
        counts[i] += 1
    return counts


def generate_ten_mcqs(chunks):
    counts = distribute_mcq_counts(len(chunks))
    all_mcqs = []
    for chunk, count in zip(chunks, counts):
        if count == 0:
            continue
        qs = generate_mcqs(chunk["text"], chunk["start"], num_questions=count)
        all_mcqs.extend(qs)
    return all_mcqs[:TOTAL_MCQS]


uploaded_file = st.file_uploader(
    "Upload a lecture video/audio file",
    type=["mp4", "mkv", "mov", "mp3", "wav", "m4a"],
)

run_button = st.button("🚀 Process Lecture", type="primary", use_container_width=True)

if run_button:
    if uploaded_file is None:
        st.error("Please upload a file first.")
    else:
        input_suffix = os.path.splitext(uploaded_file.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as tmp_input:
            tmp_input.write(uploaded_file.read())
            input_path = tmp_input.name

        extracted_audio_path = input_path + "_extracted.wav"

        try:
            with st.status("Running LectureLens pipeline...", expanded=True) as status:

                st.write("🎬 Extracting audio...")
                success, message, _ = extract_audio(input_path, extracted_audio_path)
                if not success:
                    st.error(f"Audio extraction failed: {message}")
                    st.stop()
                st.write("✅ Audio extracted")

                st.write("🎙️ Transcribing with Whisper...")
                segments = process_audio(extracted_audio_path)
                st.write(f"✅ {len(segments)} segments transcribed")

                st.write("📝 Generating subtitles...")
                base_name = os.path.splitext(uploaded_file.name)[0]
                subtitle_paths = save_subtitles(segments, filename=base_name)
                st.write("✅ Subtitles saved")

                st.write("📚 Chunking transcript...")
                chunks = chunk_transcript(segments)
                st.write(f"✅ {len(chunks)} chunks created")

                st.write("✨ Generating summaries...")
                technical_parts, simple_parts = [], []
                for chunk in chunks:
                    technical_parts.append(summarize_technical(chunk["text"]))
                    simple_parts.append(simplify_eli_junior(chunk["text"]))
                technical_summary = "\n\n".join(technical_parts)
                simple_summary = "\n\n".join(simple_parts)
                st.write("✅ Summaries generated")

                st.write(f"🧠 Generating {TOTAL_MCQS} quiz questions...")
                mcqs = generate_ten_mcqs(chunks)
                st.write(f"✅ {len(mcqs)} questions generated")

                st.write("💾 Saving to your account...")
                full_transcript = " ".join(seg["text"] for seg in segments)
                lecture_id = create_lecture(
                    user_id=st.session_state["user_id"],
                    filename=uploaded_file.name,
                    full_transcript=full_transcript,
                    technical_summary=technical_summary,
                    simple_summary=simple_summary,
                    srt_path=subtitle_paths["srt_path"],
                    vtt_path=subtitle_paths["vtt_path"],
                )
                add_transcript_segments(lecture_id, segments)
                st.write("✅ Saved to history")

                status.update(label="✅ Pipeline complete!", state="complete")

            st.session_state["last_lecture_id"] = lecture_id
            st.session_state["last_segments"] = segments
            st.session_state["last_technical_summary"] = technical_summary
            st.session_state["last_simple_summary"] = simple_summary
            st.session_state["last_mcqs"] = mcqs
            st.session_state["last_srt_path"] = subtitle_paths["srt_path"]
            st.session_state["quiz_answers"] = {}

        finally:
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(extracted_audio_path):
                os.remove(extracted_audio_path)


if "last_lecture_id" in st.session_state:
    st.divider()
    tab_transcript, tab_summary, tab_quiz, tab_download = st.tabs(
        ["📝 Transcript", "✨ Summary", "🧠 Quiz", "⬇️ Download .srt"]
    )

    with tab_transcript:
        render_transcript(st.session_state["last_segments"])

    with tab_summary:
        mode = st.radio("View mode", ["Simple (ELI-Junior)", "Technical"], horizontal=True)
        if mode == "Technical":
            st.write(st.session_state["last_technical_summary"])
        else:
            st.write(st.session_state["last_simple_summary"])

    with tab_quiz:
        mcqs = st.session_state["last_mcqs"]
        if not mcqs:
            st.warning("No quiz questions were generated.")
        else:
            with st.form("quiz_form"):
                for idx, q in enumerate(mcqs, start=1):
                    st.markdown(f"**{idx}. {q['question']}**")
                    options = q.get("options", {})
                    selected = st.radio(
                        "Choose an answer",
                        options=list(options.keys()),
                        format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                        key=f"mcq_{idx}",
                        label_visibility="collapsed",
                    )
                    st.session_state["quiz_answers"][q["question"]] = selected
                    st.divider()
                submitted = st.form_submit_button("✅ Submit Quiz", type="primary")

            if submitted:
                quiz_wrapper = {"quiz": [{"mcqs": mcqs}]}
                weak_areas = get_weak_areas(quiz_wrapper, st.session_state["quiz_answers"])
                correct = len(mcqs) - len(weak_areas)

                save_quiz_result(st.session_state["last_lecture_id"], correct, len(mcqs))

                st.success(f"Score: {correct} / {len(mcqs)} correct (saved to your history)")

                if weak_areas:
                    st.subheader("📌 Questions you got wrong")
                    for w in weak_areas:
                        st.markdown(
                            f"- **{w['question']}** — you answered `{w['your_answer']}`, "
                            f"correct was `{w['correct_answer']}`"
                        )
                else:
                    st.balloons()

    with tab_download:
        srt_path = st.session_state["last_srt_path"]
        if os.path.exists(srt_path):
            with open(srt_path, "rb") as f:
                st.download_button(
                    "⬇️ Download .srt",
                    data=f.read(),
                    file_name=os.path.basename(srt_path),
                    mime="text/plain",
                )
