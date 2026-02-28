from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
from backend.db.session import get_db
from backend.db.models import User, Config
from backend.db.sync import write_config_to_file, delete_config_file, sync_user_configs, ensure_user_dirs
from backend.core.deps import get_current_user, app_logger

router = APIRouter(prefix="/configs", tags=["configs"])


class ConfigResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True


class ConfigContent(BaseModel):
    content: str


@router.get("/", response_model=List[ConfigResponse])
def list_configs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sync_user_configs(current_user.id, current_user.username)
    configs = db.query(Config).filter(Config.user_id == current_user.id).all()
    return configs


@router.get("/{name}", response_model=ConfigContent)
def get_config(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(Config).filter(
        Config.user_id == current_user.id,
        Config.name == name
    ).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"content": config.content}


@router.put("/{name}", response_model=ConfigResponse)
def upsert_config(
    name: str,
    config: ConfigContent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    existing = db.query(Config).filter(
        Config.user_id == current_user.id,
        Config.name == name
    ).first()

    content = config.content

    if not existing:
        from pathlib import Path
        from backend.core.config import BASE_DIR, DENO_PATH
        import json

        template_path = BASE_DIR / "backend" / "templates" / "video_720p.json"
        if template_path.exists():
            try:
                template_content = json.loads(template_path.read_text())
                
                if isinstance(template_content, dict):
                    if "yt-dlp" in template_content and isinstance(template_content["yt-dlp"], dict):
                        ytdlp_args = template_content["yt-dlp"]
                        if "--download-archive" in ytdlp_args:
                            ytdlp_args["--download-archive"] = "configs/ytdl-archive.txt"
                        if "--cookies" in ytdlp_args:
                            ytdlp_args["--cookies"] = "configs/cookies.txt"
                        if "--js-runtime" in ytdlp_args:
                            deno_path = DENO_PATH if DENO_PATH else "deno"
                            ytdlp_args["--js-runtime"] = f"deno:{deno_path}"
                    else:
                        if "--download-archive" in template_content:
                            template_content["--download-archive"] = "configs/ytdl-archive.txt"
                        if "--cookies" in template_content:
                            template_content["--cookies"] = "configs/cookies.txt"
                        if "--js-runtime" in template_content:
                            deno_path = DENO_PATH if DENO_PATH else "deno"
                            template_content["--js-runtime"] = f"deno:{deno_path}"
                
                content = json.dumps(template_content, indent=2)
            except Exception as e:
                app_logger.warning(f"Failed to load template for new config {name}: {e}")

    write_config_to_file(current_user.username, name, content)

    from datetime import datetime
    if existing:
        existing.content = content
        existing.updated_at = datetime.utcnow()
    else:
        new_config = Config(
            user_id=current_user.id,
            name=name,
            content=content
        )
        db.add(new_config)

    db.commit()
    return {"name": name}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_config(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    config = db.query(Config).filter(
        Config.user_id == current_user.id,
        Config.name == name
    ).first()
    if config:
        db.delete(config)
        db.commit()

    delete_config_file(current_user.username, name)
    return None


@router.post("/cookies", status_code=status.HTTP_200_OK)
async def upload_cookies(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    import os
    filename = os.path.basename(file.filename)
    print(f"[DEBUG upload_cookies] Received filename: '{filename}'")
    if filename != "cookies.txt":
        raise HTTPException(status_code=400, detail=f"Invalid filename: '{filename}'. Only 'cookies.txt' file is allowed. Please rename your file to 'cookies.txt' and try again.")
    
    from backend.core.config import MAX_COOKIES_FILE_SIZE
    
    content = await file.read()
    if len(content) > MAX_COOKIES_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large: {len(content) / 1024 / 1024:.1f}MB. Maximum allowed size is {MAX_COOKIES_FILE_SIZE / 1024 / 1024:.0f}MB.")
    
    ensure_user_dirs(current_user.username)
    
    from backend.core.config import BASE_DIR
    cookies_dir = BASE_DIR / "data" / current_user.username / "configs"
    cookies_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = cookies_dir / "cookies.txt"
    
    file_path.write_bytes(content)
    
    app_logger.info(f"User {current_user.username} uploaded cookies.txt")
    
    return {"message": "cookies.txt uploaded successfully", "path": str(file_path)}


@router.post("/reset-archive", status_code=status.HTTP_200_OK)
def reset_archive(
    current_user: User = Depends(get_current_user)
):
    from backend.core.config import BASE_DIR
    archive_path = BASE_DIR / "data" / current_user.username / "configs" / "ytdl-archive.txt"
    
    if not archive_path.exists():
        return {"message": "Archive file does not exist, nothing to reset"}
    
    archive_path.unlink()
    app_logger.info(f"User {current_user.username} reset their download archive")
    
    return {"message": "Archive reset successfully"}
