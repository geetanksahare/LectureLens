import os
import json
import shutil
import tempfile
import time
from datetime import datetime, timezone

from api.supabase_client import supabase
from api.storage import download_video, upload_output

from api.services.rag_service import generate_and_store_embeddings
from api.services.audio_service import run_audio_extraction
from api.services.transcription_service import run_transcription
from api.services.subtitle_service import run_subtitle_generation
from api.services.summary_service import run_summary
from api.services.quiz_service import run_quiz

TIMING_LOG_PATH = os.path.join(tempfile.gettempdir(), "lecturelens_timings.json")


def log_timing(lecture_id: str, timings: dict):
    all_timings = {}
    if os.path.exists(TIMING_LOG_PATH):
        with open(TIMING_LOG_PATH, "r") as f:
            try:
                all_timings = json.load(f)
            except json.JSONDecodeError:
                all_timings = {}
    all_timings[lecture_id] = timings
    with open(TIMING_LOG_PATH, "w") as f:
        json.dump(all_timings, f, indent=2)


def update_lecture_status(lecture_id: str, status: str, error_message: str = None, full_transcript: str = None):
    update_data = {"status": status}
    if error_message is not None:
        update_data["error_message"] = error_message
    if full_transcript is not None:
        update_data["full_transcript"] = full_transcript
    if status == "done":
        update_data["processed_at"] = datetime.now(timezone.utc).isoformat()

    supabase.table("lectures").update(update_data).eq("id", lecture_id).execute()


def save_job_output(lecture_id: str, output_type: str, storage_path: str = None, content: str = None):
    supabase.table("job_outputs").insert({
        "lecture_id": lecture_id,
        "output_type": output_type,
        "storage_path": storage_path,
        "content": content,
    }).execute()


def process_lecture(lecture_id: str, user_id: str, video_storage_path: str, requested_outputs: list, filename: str):
    work_dir = tempfile.mkdtemp(prefix=f"lecture_{lecture_id}_")
    timings = {}
    pipeline_start = time.time()

    try:
        update_lecture_status(lecture_id, "processing")

        video_local_path = os.path.join(work_dir, filename)
        download_video(video_storage_path, video_local_path)

        t0 = time.time()
        audio_path = os.path.join(work_dir, "audio.wav")
        run_audio_extraction(video_local_path, audio_path)
        timings["audio_extraction_sec"] = round(time.time() - t0, 2)

        t0 = time.time()
        transcript_json_path = os.path.join(work_dir, "transcript.json")
        segments = run_transcription(audio_path, transcript_json_path, work_dir=work_dir)
        timings["transcription_sec"] = round(time.time() - t0, 2)

        if not segments:
            raise RuntimeError("Transcription produced no segments — audio may be silent or unsupported.")

        timings["audio_duration_sec"] = round(segments[-1]["end"], 2)

        update_lecture_status(lecture_id, "processing", full_transcript=json.dumps(segments, ensure_ascii=False))

        try:
            generate_and_store_embeddings(lecture_id, segments)
        except Exception as e:
            print(f"Warning: embedding generation failed for lecture {lecture_id}: {e}")

        if "transcript" in requested_outputs:
            transcript_path_local = os.path.join(work_dir, "transcript.json")
            with open(transcript_path_local, "w", encoding="utf-8") as f:
                json.dump({"segments": segments}, f, ensure_ascii=False, indent=2)
            transcript_storage_path = f"{user_id}/{lecture_id}/transcript.json"
            upload_output(transcript_path_local, transcript_storage_path, content_type="application/json")
            save_job_output(lecture_id, "transcript", storage_path=transcript_storage_path)

        if "subtitles" in requested_outputs:
            paths = run_subtitle_generation(segments, output_dir=work_dir, filename="lecture")
            srt_path = f"{user_id}/{lecture_id}/lecture.srt"
            vtt_path = f"{user_id}/{lecture_id}/lecture.vtt"
            upload_output(paths["srt_path"], srt_path, content_type="text/plain")
            upload_output(paths["vtt_path"], vtt_path, content_type="text/vtt")
            save_job_output(lecture_id, "subtitles_srt", storage_path=srt_path)
            save_job_output(lecture_id, "subtitles_vtt", storage_path=vtt_path)

        wants_summary = "summary" in requested_outputs
        wants_glossary = "glossary" in requested_outputs
        wants_quiz = "quiz" in requested_outputs

        processed = None

        t0 = time.time()

        if wants_summary or wants_glossary or wants_quiz:
            processed, glossary = run_summary(segments, include_quiz=wants_quiz)

            if wants_summary:
                summary_path_local = os.path.join(work_dir, "summary.json")
                with open(summary_path_local, "w", encoding="utf-8") as f:
                    json.dump({"chunks": processed["chunks"]}, f, ensure_ascii=False, indent=2)
                summary_storage_path = f"{user_id}/{lecture_id}/summary.json"
                upload_output(summary_path_local, summary_storage_path, content_type="application/json")
                save_job_output(lecture_id, "summary", storage_path=summary_storage_path)

            if wants_glossary:
                glossary_path_local = os.path.join(work_dir, "glossary.json")
                with open(glossary_path_local, "w", encoding="utf-8") as f:
                    json.dump({"glossary": glossary}, f, ensure_ascii=False, indent=2)
                glossary_storage_path = f"{user_id}/{lecture_id}/glossary.json"
                upload_output(glossary_path_local, glossary_storage_path, content_type="application/json")
                save_job_output(lecture_id, "glossary", storage_path=glossary_storage_path)

        if wants_quiz:
            quiz_result = run_quiz(segments, processed=processed)
            quiz_path_local = os.path.join(work_dir, "quiz.json")
            with open(quiz_path_local, "w", encoding="utf-8") as f:
                json.dump(quiz_result, f, ensure_ascii=False, indent=2)
            quiz_storage_path = f"{user_id}/{lecture_id}/quiz.json"
            upload_output(quiz_path_local, quiz_storage_path, content_type="application/json")
            save_job_output(lecture_id, "quiz", storage_path=quiz_storage_path)

        timings["llm_generation_sec"] = round(time.time() - t0, 2)
        timings["total_pipeline_sec"] = round(time.time() - pipeline_start, 2)
        log_timing(lecture_id, timings)

        update_lecture_status(lecture_id, "done")
        print(f"{'='*60}")
        print(f"✅ LECTURE PROCESSING COMPLETE — lecture_id: {lecture_id}")
        print(f"   Outputs generated: {requested_outputs}")
        print(f"   Timings: {timings}")
        print(f"{'='*60}")

    except Exception as e:
        print(f"{'='*60}")
        print(f"❌ LECTURE PROCESSING FAILED — lecture_id: {lecture_id}")
        print(f"   Error: {e}")
        print(f"{'='*60}")
        try:
            update_lecture_status(lecture_id, "failed", error_message=str(e))
        except Exception as log_error:
            print(f"Additionally failed to log the error to Supabase: {log_error}")
        raise

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)