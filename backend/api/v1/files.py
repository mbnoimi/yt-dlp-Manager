# TODO: Consider using "SVAR Svelte File Manager" frontend component for better UX
# https://github.com/sVAR-Svelte-File-Manager/svar-svelte-file-manager
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from backend.core.deps import get_current_user
from backend.db.models import User
import os
from pathlib import Path
from typing import Optional

router = APIRouter()

DATA_ROOT = Path("data")


def format_file_info(path: str, base_path: Path):
    full_path = base_path / path
    if not full_path.exists():
        return None

    is_dir = full_path.is_dir()
    size = 0 if is_dir else full_path.stat().st_size
    modified = full_path.stat().st_mtime

    return {
        "path": path,
        "is_dir": is_dir,
        "size": size,
        "modified": str(modified)
    }


def require_admin(user: User = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@router.get("/avatar/{username}/{filename}")
def get_avatar(username: str, filename: str):
    avatar_path = f"data/{username}/avatar/{filename}"
    if not os.path.exists(avatar_path):
        raise HTTPException(status_code=404, detail="Avatar not found")
    return FileResponse(avatar_path)


@router.get("/files/")
def list_files(
    path: str = Query("", description="Relative path from user's downloads folder"),
    current_user: User = Depends(get_current_user)
):
    user_downloads_path = Path(f"data/{current_user.username}/downloads") / path
    files = []
    
    if not user_downloads_path.exists():
        return files
    
    if not user_downloads_path.is_dir():
        return files
    
    for item in os.listdir(user_downloads_path):
        info = format_file_info(f"{path}/{item}" if path else item, Path(f"data/{current_user.username}/downloads"))
        if info:
            files.append(info)
    
    return files


@router.get("/admin/files/")
def list_all_files(
    path: str = Query("", description="Relative path from data folder"),
    offset: int = Query(0, description="Number of items to skip"),
    limit: int = Query(50, description="Number of items to return"),
    current_user: User = Depends(require_admin)
):
    base_path = DATA_ROOT / path if path else DATA_ROOT
    all_files = []
    
    if not base_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not base_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    try:
        for item in sorted(os.listdir(base_path)):
            item_path = f"{path}/{item}" if path else item
            info = format_file_info(item_path, DATA_ROOT)
            if info:
                all_files.append(info)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    total = len(all_files)
    files = all_files[offset:offset + limit]
    
    return {
        "files": files,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + limit < total
    }

@router.post("/files/rename")
def rename_file(old_path: str, new_path: str, current_user: User = Depends(get_current_user)):
    base_path = f"data/{current_user.username}/downloads"
    old_full = os.path.join(base_path, old_path)
    new_full = os.path.join(base_path, new_path)
    
    if not os.path.exists(old_full):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.abspath(old_full).startswith(os.path.abspath(base_path)):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    os.rename(old_full, new_full)
    return {"success": True}

@router.delete("/files/{path:path}")
def delete_file(path: str, current_user: User = Depends(get_current_user)):
    base_path = f"data/{current_user.username}/downloads"
    full_path = os.path.join(base_path, path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if not os.path.abspath(full_path).startswith(os.path.abspath(base_path)):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if os.path.isdir(full_path):
        import shutil
        shutil.rmtree(full_path)
    else:
        os.remove(full_path)
    
    return {"success": True}


@router.delete("/admin/files/{path:path}")
def admin_delete_file(path: str, current_user: User = Depends(require_admin)):
    full_path = DATA_ROOT / path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not str(full_path.absolute()).startswith(str(DATA_ROOT.absolute())):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if full_path.is_dir():
        import shutil
        shutil.rmtree(full_path)
    else:
        os.remove(full_path)
    
    return {"success": True}


@router.post("/admin/files/rename")
def admin_rename_file(
    old_path: str, 
    new_path: str, 
    current_user: User = Depends(require_admin)
):
    old_full = DATA_ROOT / old_path
    new_full = DATA_ROOT / new_path
    
    if not old_full.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not str(old_full.absolute()).startswith(str(DATA_ROOT.absolute())):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    os.rename(old_full, new_full)
    return {"success": True}


@router.get("/admin/files/download/{path:path}")
def admin_download_file(
    path: str, 
    current_user: User = Depends(require_admin)
):
    full_path = DATA_ROOT / path
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if full_path.is_dir():
        raise HTTPException(status_code=400, detail="Cannot download directory")
    
    if not str(full_path.absolute()).startswith(str(DATA_ROOT.absolute())):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    return FileResponse(
        full_path, 
        filename=full_path.name,
        media_type='application/octet-stream'
    )
