from fastapi import APIRouter, Depends, HTTPException
from backend.core.deps import get_current_user, app_logger
from backend.db.models import User
import os

router = APIRouter()

@router.get("/logs/user")
def get_user_logs(current_user: User = Depends(get_current_user)):
    user_data_path = f"data/{current_user.username}/logs/user.log"
    if os.path.exists(user_data_path):
        with open(user_data_path, "r") as f:
            return f.read()
    return ""

@router.get("/logs/backend")
def get_backend_logs(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        return {"detail": "Admin only"}, 403
    backend_log_path = "backend/logs/app.log"
    if os.path.exists(backend_log_path):
        with open(backend_log_path, "r") as f:
            return f.read()
    return ""

@router.get("/logs/server")
def get_server_logs(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    backend_log_path = "backend/logs/app.log"
    if os.path.exists(backend_log_path):
        with open(backend_log_path, "r") as f:
            return f.read()
    return ""

@router.get("/logs/by-user/{username}")
def get_user_logs_by_username(username: str, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    user_data_path = f"data/{username}/logs/user.log"
    if os.path.exists(user_data_path):
        with open(user_data_path, "r") as f:
            return f.read()
    return ""
