from typing import List, Optional
from datetime import datetime
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import User, ScheduledTask
from backend.core.deps import get_current_user
from backend.services.scheduler import validate_cron_expression, get_next_run_time, delete_old_files

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ScheduledTaskCreate(BaseModel):
    name: str
    task_type: str
    datasource: Optional[str] = None
    cron_expression: str
    config: Optional[str] = None
    target_user_id: Optional[int] = None


class ScheduledTaskUpdate(BaseModel):
    name: Optional[str] = None
    task_type: Optional[str] = None
    datasource: Optional[str] = None
    cron_expression: Optional[str] = None
    config: Optional[str] = None
    is_active: Optional[bool] = None


class ScheduledTaskResponse(BaseModel):
    id: int
    user_id: int
    name: str
    task_type: str
    datasource: Optional[str] = None
    cron_expression: str
    config: Optional[str] = None
    is_active: bool
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DeleteOldFilesRequest(BaseModel):
    days: int


class DeleteOldFilesResponse(BaseModel):
    files_deleted: int
    folders_deleted: int
    space_freed: int


@router.get("/", response_model=List[ScheduledTaskResponse])
def list_scheduled_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tasks = db.query(ScheduledTask).filter(
        ScheduledTask.user_id == current_user.id
    ).all()
    return tasks


@router.post("/", response_model=ScheduledTaskResponse)
def create_scheduled_task(
    task: ScheduledTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.db.models import Config, UrlSource
    
    if task.task_type not in ["download", "cleanup"]:
        raise HTTPException(status_code=400, detail="task_type must be 'download' or 'cleanup'")
    
    if task.task_type == "download" and not task.datasource:
        raise HTTPException(status_code=400, detail="datasource is required for download tasks")
    
    target_user = current_user
    target_user_id = current_user.id
    
    if current_user.is_admin and task.target_user_id:
        target_user = db.query(User).filter(User.id == task.target_user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target user not found")
        target_user_id = task.target_user_id
    
    if not validate_cron_expression(task.cron_expression):
        raise HTTPException(status_code=400, detail="Invalid cron expression")

    if task.task_type == "download":
        config = db.query(Config).filter(
            Config.user_id == target_user_id,
            Config.name == task.datasource
        ).first()
        urls = db.query(UrlSource).filter(
            UrlSource.user_id == target_user_id,
            UrlSource.name == task.datasource
        ).first()

        if not config or not urls:
            raise HTTPException(status_code=404, detail="Datasource not found")

    next_run = get_next_run_time(task.cron_expression)
    
    db_task = ScheduledTask(
        user_id=target_user_id,
        name=task.name,
        task_type=task.task_type,
        datasource=task.datasource,
        cron_expression=task.cron_expression,
        config=task.config,
        next_run=next_run
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return db_task


@router.get("/{task_id}", response_model=ScheduledTaskResponse)
def get_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return task


@router.put("/{task_id}", response_model=ScheduledTaskResponse)
def update_scheduled_task(
    task_id: int,
    task_update: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if task_update.cron_expression is not None:
        if not validate_cron_expression(task_update.cron_expression):
            raise HTTPException(status_code=400, detail="Invalid cron expression")
        task.cron_expression = task_update.cron_expression
        task.next_run = get_next_run_time(task_update.cron_expression)
    
    if task_update.name is not None:
        task.name = task_update.name
    
    if task_update.task_type is not None:
        if task_update.task_type not in ["download", "cleanup"]:
            raise HTTPException(status_code=400, detail="task_type must be 'download' or 'cleanup'")
        task.task_type = task_update.task_type
    
    if task_update.datasource is not None:
        from backend.db.models import Config, UrlSource
        config = db.query(Config).filter(
            Config.user_id == task.user_id,
            Config.name == task_update.datasource
        ).first()
        urls = db.query(UrlSource).filter(
            UrlSource.user_id == task.user_id,
            UrlSource.name == task_update.datasource
        ).first()

        if not config or not urls:
            raise HTTPException(status_code=404, detail="Datasource not found")
        task.datasource = task_update.datasource
    
    if task_update.config is not None:
        task.config = task_update.config
    
    if task_update.is_active is not None:
        task.is_active = task_update.is_active
        if task.is_active:
            task.next_run = get_next_run_time(task.cron_expression)
        else:
            task.next_run = None
    
    db.commit()
    db.refresh(task)
    
    return task


@router.delete("/{task_id}", status_code=204)
def delete_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not current_user.is_admin and task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(task)
    db.commit()
    
    return None


@router.post("/cleanup", response_model=DeleteOldFilesResponse)
def cleanup_old_files(
    request: DeleteOldFilesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if request.days < 1:
        raise HTTPException(status_code=400, detail="Days must be at least 1")
    
    from backend.services.scheduler import delete_old_files as do_delete
    result = do_delete(current_user.id, request.days, current_user.username)
    
    return result


@router.get("/cleanup/count")
def count_old_files(
    days: int = Query(30, ge=1, description="Number of days"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    import os
    from pathlib import Path
    
    downloads_path = Path(f"data/{current_user.username}/downloads")
    if not downloads_path.exists():
        return {"files_count": 0, "folders_count": 0, "total_size": 0}
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    files_count = 0
    folders_count = 0
    total_size = 0
    
    for root, dirs, files in os.walk(downloads_path):
        root_path = Path(root)
        
        for file in files:
            file_path = root_path / file
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    files_count += 1
                    total_size += file_path.stat().st_size
            except Exception:
                pass
        
        for dir_name in dirs:
            dir_path = root_path / dir_name
            try:
                if dir_path.exists() and not any(dir_path.iterdir()):
                    if dir_path.stat().st_mtime < cutoff_time:
                        folders_count += 1
            except Exception:
                pass
    
    return {
        "files_count": files_count,
        "folders_count": folders_count,
        "total_size": total_size
    }


@router.get("/admin/tasks", response_model=List[ScheduledTaskResponse])
def list_all_scheduled_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    tasks = db.query(ScheduledTask).all()
    return tasks
