import asyncio
import uuid
import hashlib

from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException, BackgroundTasks
from starlette.requests import ClientDisconnect
from api.deps import get_current_user
from api.supabase_client import supabase
from api.storage import upload_video, copy_video, copy_output
from api.job_processor import process_lecture, save_job_output



router = APIRouter()


@router.post("/lectures")
async def create_lecture(
    request: Request,
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

    # --- NEW: handle the client cancelling mid-upload (Cancel button on the frontend) ---
    # When the browser aborts the fetch, Starlette raises ClientDisconnect (or the OS
    # resets the connection) while we're still reading the body. Catch it here so it
    # never surfaces as a 500 / unhandled traceback — the client is already gone, so
    # there is nothing useful to return, and nothing should be saved.
    try:
        file_bytes = await file.read()
    except ClientDisconnect:
        print(f"⚠️  Upload cancelled by client before it finished (user_id={user_id}). Nothing saved.")
        return
    except (ConnectionResetError, asyncio.CancelledError):
        print(f"⚠️  Upload connection dropped/cancelled by client (user_id={user_id}). Nothing saved.")
        return
    # --- END NEW ---

    # --- NEW: size validation ---
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {len(file_bytes) / (1024*1024*1024):.2f}GB. Max allowed: {MAX_FILE_SIZE_BYTES / (1024*1024*1024):.0f}GB",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    # --- END NEW ---

    # --- NEW: catch the case where the client cancelled right after the body
    # finished but before we've done anything with it yet ---
    if await request.is_disconnected():
        print(f"⚠️  Client disconnected right after upload finished (user_id={user_id}). Aborting before saving.")
        return
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

        # Reuse the same video file already in B2 — no copy needed, saves storage
        shared_video_path = source_lecture["video_storage_path"]

        try:
            new_lecture_result = supabase.table("lectures").insert({
                "user_id": user_id,
                "filename": file.filename,
                "video_storage_path": shared_video_path,
                "requested_outputs": outputs_list,
                "status": "done",
                "content_hash": content_hash,
            }).execute()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create lecture record: {str(e)}")

        new_lecture = new_lecture_result.data[0]
        new_lecture_id = new_lecture["id"]

        # Point this user's outputs at the same generated files — no copy needed
        source_outputs = (
            supabase.table("job_outputs")
            .select("output_type, storage_path, content")
            .eq("lecture_id", source_lecture_id)
            .execute()
        )

        for output in source_outputs.data:
            save_job_output(
                new_lecture_id,
                output["output_type"],
                storage_path=output["storage_path"],
                content=output["content"],
            )

        print(f"{'='*60}")
        print(f"✅ DUPLICATE DETECTED (cross-user) — new lecture_id: {new_lecture_id}")
        print(f"   Reusing shared video + outputs from lecture_id: {source_lecture_id} (no storage duplicated)")
        print(f"{'='*60}")
        return {
            "lecture_id": new_lecture_id,
            "status": "done",
            "message": "This video was already processed by another user. Reused existing results instead of reprocessing.",
            "duplicate": True,
        }

    # --- NEW: one more disconnect check right before the expensive B2 upload ---
    if await request.is_disconnected():
        print(f"⚠️  Client disconnected before storage upload started (user_id={user_id}). Skipping.")
        return
    # --- END NEW ---

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