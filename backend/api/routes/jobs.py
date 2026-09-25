from fastapi import APIRouter, Depends, HTTPException
from api.deps import get_current_user
from api.supabase_client import supabase
from api.storage import get_output_signed_url

router = APIRouter()


@router.get("/lectures")
def list_lectures(user_id: str = Depends(get_current_user)):
    result = (
        supabase.table("lectures")
        .select("id, filename, status, requested_outputs, error_message, processed_at")
        .eq("user_id", user_id)
        .order("processed_at", desc=True)
        .execute()
    )
    return {"lectures": result.data}


@router.get("/lectures/{lecture_id}")
def get_lecture(lecture_id: str, user_id: str = Depends(get_current_user)):
    lecture_result = (
        supabase.table("lectures")
        .select("*")
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .execute()
    )

    if not lecture_result.data:
        raise HTTPException(status_code=404, detail="Lecture not found")

    lecture = lecture_result.data[0]

    response = {
        "lecture_id": lecture["id"],
        "filename": lecture["filename"],
        "status": lecture["status"],
        "requested_outputs": lecture["requested_outputs"],
        "error_message": lecture["error_message"],
        "processed_at": lecture["processed_at"],
        "progress_pct": lecture.get("progress_pct", 0),
        "progress_stage": lecture.get("progress_stage"),
        "processing_seconds": lecture.get("processing_seconds"),
        "outputs": {},
    }

    if lecture["status"] != "done":
        return response

    outputs_result = (
        supabase.table("job_outputs")
        .select("output_type, storage_path, content")
        .eq("lecture_id", lecture_id)
        .execute()
    )

    for output in outputs_result.data:
        output_type = output["output_type"]
        if output["storage_path"]:
            try:
                signed_url = get_output_signed_url(output["storage_path"])
            except Exception:
                signed_url = None
            response["outputs"][output_type] = {"url": signed_url}
        elif output["content"]:
            response["outputs"][output_type] = {"content": output["content"]}

    return response