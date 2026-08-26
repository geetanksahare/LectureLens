from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from api.deps import get_current_user
from api.supabase_client import supabase
from api.storage import upload_video
from api.job_processor import process_lecture

router = APIRouter()


@router.post("/lectures")
async def create_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    requested_outputs: str = Form(...),
    user_id: str = Depends(get_current_user),
):
    outputs_list = [o.strip() for o in requested_outputs.split(",") if o.strip()]
    valid_outputs = {"subtitles", "summary", "quiz"}
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