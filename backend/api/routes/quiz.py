import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.deps import get_current_user
from api.supabase_client import supabase
from api.storage import download_output
from api.services.quiz_grading_service import grade_submission

router = APIRouter()


class QuizSubmission(BaseModel):
    mcq_answers: dict[str, str] = {}
    short_answers: dict[str, str] = {}


@router.post("/quiz/{lecture_id}/submit")
def submit_quiz(lecture_id: str, submission: QuizSubmission, user_id: str = Depends(get_current_user)):
    lecture_result = (
        supabase.table("lectures")
        .select("id, status")
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not lecture_result.data:
        raise HTTPException(status_code=404, detail="Lecture not found")

    if lecture_result.data[0]["status"] != "done":
        raise HTTPException(status_code=400, detail="Lecture processing is not complete yet")

    quiz_output_result = (
        supabase.table("job_outputs")
        .select("storage_path")
        .eq("lecture_id", lecture_id)
        .eq("output_type", "quiz")
        .execute()
    )
    if not quiz_output_result.data:
        raise HTTPException(status_code=404, detail="No quiz was generated for this lecture")

    storage_path = quiz_output_result.data[0]["storage_path"]

    try:
        quiz_bytes = download_output(storage_path)
        quiz_data = json.loads(quiz_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load quiz data: {str(e)}")

    score, total_questions, detailed_results, weak_areas = grade_submission(
        quiz_data, submission.mcq_answers, submission.short_answers
    )

    try:
        supabase.table("quiz_results").insert({
            "lecture_id": lecture_id,
            "score": score,
            "total_questions": total_questions,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save quiz result: {str(e)}")

    return {
        "lecture_id": lecture_id,
        "score": score,
        "total_questions": total_questions,
        "results": detailed_results,
        "weak_areas": weak_areas,
    }