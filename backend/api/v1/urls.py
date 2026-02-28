from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import User, UrlSource
from backend.db.sync import write_urls_to_file, delete_urls_file, sync_user_urls
from backend.core.deps import get_current_user

router = APIRouter(prefix="/urls", tags=["urls"])


class UrlSourceResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True


class UrlSourceContent(BaseModel):
    content: str


@router.get("/", response_model=List[UrlSourceResponse])
def list_url_sources(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sync_user_urls(current_user.id, current_user.username)
    sources = db.query(UrlSource).filter(UrlSource.user_id == current_user.id).all()
    return sources


@router.get("/{name}", response_model=UrlSourceContent)
def get_url_source(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(UrlSource).filter(
        UrlSource.user_id == current_user.id,
        UrlSource.name == name
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="URL source not found")
    return {"content": source.content}


@router.put("/{name}", response_model=UrlSourceResponse)
def upsert_url_source(
    name: str,
    source: UrlSourceContent,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    write_urls_to_file(current_user.username, name, source.content)

    existing = db.query(UrlSource).filter(
        UrlSource.user_id == current_user.id,
        UrlSource.name == name
    ).first()

    from datetime import datetime
    if existing:
        existing.content = source.content
        existing.updated_at = datetime.utcnow()
    else:
        new_source = UrlSource(
            user_id=current_user.id,
            name=name,
            content=source.content
        )
        db.add(new_source)

    db.commit()
    return {"name": name}


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_url_source(name: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    source = db.query(UrlSource).filter(
        UrlSource.user_id == current_user.id,
        UrlSource.name == name
    ).first()
    if source:
        db.delete(source)
        db.commit()

    delete_urls_file(current_user.username, name)
    return None
