import os
import json
import shutil
import tempfile
from datetime import datetime, timezone

from api.supabase_client import supabase
from api.storage import download_video, upload_output

from api.services.audio_service import run_audio_extraction
from api.services.transcription_service import run_transcription
from api.services.subtitle_service import run_subtitle_generation
from api.services.summary_service import run_summary
from api.services.quiz_service import run_quiz

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

    try:
        update_lecture_status(lecture_id, "processing")

        video_local_path = os.path.join(work_dir, filename)
        download_video(video_storage_path, video_local_path)

        audio_path = os.path.join(work_dir, "audio.wav")
        run_audio_extraction(video_local_path, audio_path)

        transcript_json_path = os.path.join(work_dir, "transcript.json")
        segments = run_transcription(audio_path, transcript_json_path)

        if not segments:
            raise RuntimeError("Transcription produced no segments — audio may be silent or unsupported.")

        update_lecture_status(lecture_id, "processing", full_transcript=json.dumps(segments, ensure_ascii=False))

        if "subtitles" in requested_outputs:
            paths = run_subtitle_generation(segments, output_dir=work_dir, filename="lecture")
            srt_path = f"{user_id}/{lecture_id}/lecture.srt"
            vtt_path = f"{user_id}/{lecture_id}/lecture.vtt"
            upload_output(paths["srt_path"], srt_path, content_type="text/plain")
            upload_output(paths["vtt_path"], vtt_path, content_type="text/vtt")
            save_job_output(lecture_id, "subtitles_srt", storage_path=srt_path)
            save_job_output(lecture_id, "subtitles_vtt", storage_path=vtt_path)

        if "summary" in requested_outputs:
            processed, glossary = run_summary(segments)
            summary_path_local = os.path.join(work_dir, "summary.json")
            with open(summary_path_local, "w", encoding="utf-8") as f:
                json.dump({"chunks": processed["chunks"], "glossary": glossary}, f, ensure_ascii=False, indent=2)
            summary_storage_path = f"{user_id}/{lecture_id}/summary.json"
            upload_output(summary_path_local, summary_storage_path, content_type="application/json")
            save_job_output(lecture_id, "summary", storage_path=summary_storage_path)

        if "quiz" in requested_outputs:
            quiz_result = run_quiz(segments)
            quiz_path_local = os.path.join(work_dir, "quiz.json")
            with open(quiz_path_local, "w", encoding="utf-8") as f:
                json.dump(quiz_result, f, ensure_ascii=False, indent=2)
            quiz_storage_path = f"{user_id}/{lecture_id}/quiz.json"
            upload_output(quiz_path_local, quiz_storage_path, content_type="application/json")
            save_job_output(lecture_id, "quiz", storage_path=quiz_storage_path)

        update_lecture_status(lecture_id, "done")

    except Exception as e:
        update_lecture_status(lecture_id, "failed", error_message=str(e))
        raise

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)