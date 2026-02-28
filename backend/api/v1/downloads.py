from typing import List, Optional
from datetime import datetime
import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import User, Config, UrlSource, DownloadJob
from backend.services.downloader import start_download_job, stop_download_job, get_running_jobs
from backend.core.deps import get_current_user, get_current_user_optional, get_current_user_from_query

router = APIRouter(prefix="/downloads", tags=["downloads"])


class DownloadSourceResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True


class DownloadRequest(BaseModel):
    create_symlinks: Optional[bool] = True


class JobStatusResponse(BaseModel):
    id: int
    name: str
    status: str
    create_symlinks: bool
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


@router.get(
    "/",
    response_model=List[DownloadSourceResponse],
    summary="List available download sources",
    description="""
List download sources that have both a config and URL source defined.

Only names that exist in both configs and URLs are returned.
Use these names with POST /{name} to start a download job.
"""
)
def list_download_sources(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config_names = set()
    url_names = set()

    configs = db.query(Config).filter(Config.user_id == current_user.id).all()
    urls = db.query(UrlSource).filter(UrlSource.user_id == current_user.id).all()

    for c in configs:
        config_names.add(c.name)
    for u in urls:
        url_names.add(u.name)

    common_names = config_names & url_names
    return [{"name": name} for name in sorted(common_names)]


@router.post(
    "/{name}",
    response_model=JobStatusResponse,
    summary="Start a download job",
    description="""
Start a download job using the specified config and URL sources.

**Queue Behavior:**
- Jobs are queued if maximum concurrent downloads (MAX_CONCURRENT_DOWNLOADS) is reached
- Each user can only have 1 running job at a time
- Use GET /running (SSE) to monitor job status in real-time

**Request body:**
- `create_symlinks` (bool, optional): Whether to create symlinks for deduplicated files. Default: true

**Response:**
- Returns immediately with job status
- Status can be: "pending", "running", "completed", "failed"
"""
)
def start_download(
    name: str,
    request: DownloadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.core.deps import app_logger
    
    config = db.query(Config).filter(
        Config.user_id == current_user.id,
        Config.name == name
    ).first()
    urls = db.query(UrlSource).filter(
        UrlSource.user_id == current_user.id,
        UrlSource.name == name
    ).first()

    if not config or not urls:
        raise HTTPException(status_code=404, detail="Config or URLs not found for this name")
    
    app_logger.info(f"Starting download job for user {current_user.username}, config={name}, create_symlinks={request.create_symlinks}")

    try:
        job_id = start_download_job(
            username=current_user.username,
            user_id=current_user.id,
            config_name=name,
            urls_name=name,
            create_symlinks=bool(request.create_symlinks)
        )

        db.expire_all()
        job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
        
        if not job:
            return {"id": job_id, "name": f"{name}/{name}", "status": "pending", 
                    "create_symlinks": bool(request.create_symlinks),
                    "started_at": datetime.utcnow(), "finished_at": None, "error_message": None}
        
        return job
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        app_logger.error(f"Error starting download: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error starting download: {str(e)}")


@router.get("/status/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(DownloadJob).filter(
        DownloadJob.id == job_id,
        DownloadJob.user_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/stop/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def stop_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not current_user.is_admin and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to stop this job")

    stop_download_job(job_id)
    return None


@router.post("/cancel/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_pending_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if not current_user.is_admin and job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this job")
    
    if job.status != "pending":
        raise HTTPException(status_code=400, detail="Can only cancel pending jobs")

    job.status = "failed"
    job.error_message = "Cancelled by user"
    db.commit()
    
    return None


@router.post("/stop-all", status_code=status.HTTP_204_NO_CONTENT)
def stop_all_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    running_jobs = db.query(DownloadJob).filter(DownloadJob.status == "running").all()
    for job in running_jobs:
        stop_download_job(job.id)

    pending_jobs = db.query(DownloadJob).filter(DownloadJob.status == "pending").all()
    for job in pending_jobs:
        job.status = "failed"
        job.error_message = "Stopped by admin"
    db.commit()
    
    return None


@router.post("/cancel-all", status_code=status.HTTP_204_NO_CONTENT)
def cancel_all_pending_jobs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pending_jobs = db.query(DownloadJob).filter(
        DownloadJob.status == "pending",
        DownloadJob.user_id == current_user.id
    ).all()
    
    for job in pending_jobs:
        job.status = "failed"
        job.error_message = "Cancelled by user"
    db.commit()
    
    return None



@router.get(
    "/running",
    summary="Stream running downloads (SSE)",
    description="""
Server-Sent Events (SSE) endpoint for real-time download job status.

**Behavior:**
- Admin users see all running jobs across all users
- Regular users see only their own running job

**Response format:**
```json
[
  {
    "id": 1,
    "name": "config/urls",
    "user_id": 1,
    "started_at": "2024-01-01T00:00:00",
    "create_symlinks": true,
    "current_url": "https://youtube.com/..."  // only for non-admin users
  }
]
```

**Client usage:**
```javascript
const eventSource = new EventSource('/api/v1/downloads/running');
eventSource.onmessage = (event) => {
  const jobs = JSON.parse(event.data);
  console.log(jobs);
};
```
""",
    response_class=StreamingResponse,
    responses={
        200: {
            "description": "Server-Sent Events stream of running download jobs",
            "content": {
                "text/event-stream": {
                    "schema": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                                "user_id": {"type": "integer"},
                                "started_at": {"type": "string", "format": "date-time"},
                                "create_symlinks": {"type": "boolean"},
                                "current_url": {"type": "string", "nullable": True}
                            }
                        }
                    },
                    "example": [
                        {
                            "id": 1,
                            "name": "yt-kids/yt-kids",
                            "user_id": 2,
                            "started_at": "2024-01-01T00:00:00",
                            "create_symlinks": True,
                            "current_url": "https://youtube.com/watch?v=xxx"
                        }
                    ]
                }
            }
        }
    }
)
def stream_running_downloads(
    token: Optional[str] = Query(None, description="JWT token for authentication"),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_query(token, db)
    if current_user is None:
        async def unauthorized():
            yield ""
        return StreamingResponse(unauthorized(), status_code=401)
    async def generator():
        while True:
            if current_user.is_admin:
                jobs = db.query(DownloadJob).filter(
                    DownloadJob.status == "running"
                ).all()
                
                job_list = []
                for job in jobs:
                    job_list.append({
                        "id": job.id,
                        "name": job.name,
                        "user_id": job.user_id,
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "create_symlinks": job.create_symlinks,
                    })
            else:
                job = db.query(DownloadJob).filter(
                    DownloadJob.user_id == current_user.id,
                    DownloadJob.status == "running"
                ).first()
                
                job_list = []
                if job:
                    running_info = get_running_jobs(current_user.id)
                    current_url = None
                    for info in running_info:
                        if info["id"] == job.id:
                            current_url = info.get("current_url")
                            break
                    
                    job_list.append({
                        "id": job.id,
                        "name": job.name,
                        "user_id": job.user_id,
                        "started_at": job.started_at.isoformat() if job.started_at else None,
                        "create_symlinks": job.create_symlinks,
                        "current_url": current_url,
                    })
            
            yield f"data: {json.dumps(job_list)}\n\n"
            await asyncio.sleep(2)
    
    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/users-with-jobs")
def get_users_with_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    running_jobs = db.query(DownloadJob).filter(
        DownloadJob.status == "running"
    ).all()
    
    users_with_jobs = []
    for job in running_jobs:
        user = db.query(User).filter(User.id == job.user_id).first()
        if user:
            users_with_jobs.append({
                "user_id": user.id,
                "username": user.username,
                "job_id": job.id,
                "job_name": job.name,
                "started_at": job.started_at.isoformat() if job.started_at else None,
            })
    
    return users_with_jobs
