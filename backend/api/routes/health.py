from fastapi import APIRouter
from api.supabase_client import supabase

router = APIRouter()

@router.get("/health")
def health_check():
    try:
        # cheap query — just confirms the DB connection + key work
        supabase.table("profiles").select("id").limit(1).execute()
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok",
        "supabase": db_status,
    }
    
from fastapi import Depends
from api.deps import get_current_user

@router.get("/whoami")
def whoami(user_id: str = Depends(get_current_user)):
    return {"user_id": user_id}