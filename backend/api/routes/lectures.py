import uuid
import hashlib

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from api.deps import get_current_user
from api.supabase_client import supabase
from api.storage import upload_video, copy_video, copy_output
from api.job_processor import process_lecture, save_job_output



router = APIRouter()


@router.post("/lectures")
async def create_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    requested_outputs: str = Form(...),
    user_id: str = Depends(get_current_user),
):
    outputs_list = [o.strip() for o in requested_outputs.split(",") if o.strip()]
    valid_outputs = {"transcript", "subtitles", "summary", "glossary", "quiz"}
    invalid = [o for o in outputs_list if o not in valid_outputs]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid output types: {invalid}")

    # --- NEW: format validation ---
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Only video files are accepted.",
        )

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 * 1024  # 10 GB

    file_bytes = await file.read()

    # --- NEW: size validation ---
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(file_bytes) / (1024*1024*1024):.2f}GB. Max allowed: {MAX_FILE_SIZE_BYTES / (1024*1024*1024):.0f}GB",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    # --- END NEW ---
    
    content_hash = hashlib.sha256(file_bytes).hexdigest()

    # Case 1: this same user already has this exact file processed
    own_existing = (
        supabase.table("lectures")
        .select("id, status, filename, requested_outputs")
        .eq("user_id", user_id)
        .eq("content_hash", content_hash)
        .eq("status", "done")
        .execute()
    )

    if own_existing.data:
        existing_lecture = own_existing.data[0]
        print(f"{'='*60}")
        print(f"✅ DUPLICATE DETECTED (same user) — reusing lecture_id: {existing_lecture['id']}")
        print(f"   No reprocessing needed — instant response.")
        print(f"{'='*60}")
        return {
            "lecture_id": existing_lecture["id"],
            "status": "done",
            "message": "This exact video was already uploaded and processed. Returning existing results instead of reprocessing.",
            "duplicate": True,
        }

    # Case 2: a different user already processed this exact file — reuse their outputs
    other_existing = (
        supabase.table("lectures")
        .select("id, video_storage_path, status")
        .eq("content_hash", content_hash)
        .eq("status", "done")
        .limit(1)
        .execute()
    )

    if other_existing.data:
        source_lecture = other_existing.data[0]
        source_lecture_id = source_lecture["id"]

        # Give this user their own private copy of the video
        new_video_path = f"{user_id}/{uuid.uuid4()}_{file.filename}"
        try:
            copy_video(source_lecture["video_storage_path"], new_video_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to copy video for deduplication: {str(e)}")

        # Create a new lectures row for this user, immediately marked done
        try:
            new_lecture_result = supabase.table("lectures").insert({
                "user_id": user_id,
                "filename": file.filename,
                "video_storage_path": new_video_path,
                "requested_outputs": outputs_list,
                "status": "done",
                "content_hash": content_hash,
            }).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create lecture record: {str(e)}")

        new_lecture = new_lecture_result.data[0]
        new_lecture_id = new_lecture["id"]

        # Copy each existing output into this user's own output folder
        source_outputs = (
            supabase.table("job_outputs")
            .select("output_type, storage_path, content")
            .eq("lecture_id", source_lecture_id)
            .execute()
        )

        for output in source_outputs.data:
            if output["storage_path"]:
                filename_part = output["storage_path"].split("/")[-1]
                new_output_path = f"{user_id}/{new_lecture_id}/{filename_part}"
                try:
                    copy_output(output["storage_path"], new_output_path)
                    save_job_output(new_lecture_id, output["output_type"], storage_path=new_output_path)
                except Exception:
                    continue  # skip any output that fails to copy rather than failing the whole request
            elif output["content"]:
                save_job_output(new_lecture_id, output["output_type"], content=output["content"])

        print(f"{'='*60}")
        print(f"✅ DUPLICATE DETECTED (cross-user) — new lecture_id: {new_lecture_id}")
        print(f"   Outputs copied from lecture_id: {source_lecture_id}")
        print(f"{'='*60}")
        return {
            "lecture_id": new_lecture_id,
            "status": "done",
            "message": "This video was already processed by another user. Reused existing results instead of reprocessing.",
            "duplicate": True,
        }

    try:
        storage_path = upload_video(user_id, file.filename, file_bytes, content_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video upload failed: {str(e)}")

    try:
        result = supabase.table("lectures").insert({
            "user_id": user_id,
            "filename": file.filename,
            "video_storage_path": storage_path,
            "requested_outputs": outputs_list,
            "status": "queued",
            "content_hash": content_hash,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lecture record: {str(e)}")

    lecture = result.data[0]

    background_tasks.add_task(
        process_lecture,
        lecture_id=lecture["id"],
        user_id=user_id,
        video_storage_path=storage_path,
        requested_outputs=outputs_list,
        filename=file.filename,
    )

    return {
        "lecture_id": lecture["id"],
        "status": lecture["status"],
        "message": "Lecture uploaded and queued for processing.",
    }