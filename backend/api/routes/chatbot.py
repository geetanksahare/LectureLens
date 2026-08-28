from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.deps import get_current_user
from api.supabase_client import supabase
from api.services.rag_service import answer_question

router = APIRouter()


class QuestionRequest(BaseModel):
    question: str


@router.post("/lectures/{lecture_id}/ask")
def ask_question(lecture_id: str, request: QuestionRequest, user_id: str = Depends(get_current_user)):
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

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = answer_question(lecture_id, request.question.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

    return {
        "lecture_id": lecture_id,
        "question": request.question,
        "answer": result["answer"],
        "source": result["source"],
        "timestamps": result["timestamps"],
    }