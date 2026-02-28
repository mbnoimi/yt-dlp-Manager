import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import User
from backend.core.security import decode_access_token
from backend.core.config import LOGS_DIR, DATA_DIR, MAX_LOG_FILE_SIZE, LOG_BACKUP_COUNT

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            LOGS_DIR / "app.log",
            maxBytes=MAX_LOG_FILE_SIZE,
            backupCount=LOG_BACKUP_COUNT
        ),
        logging.StreamHandler()
    ]
)

app_logger = logging.getLogger("app")

_user_loggers = {}


def get_user_logger(username: str) -> logging.Logger:
    if username not in _user_loggers:
        user_log_dir = DATA_DIR / username / "logs"
        user_log_dir.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(f"user.{username}")
        logger.setLevel(logging.INFO)
        logger.handlers = []
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        handler = RotatingFileHandler(
            user_log_dir / "user.log",
            maxBytes=MAX_LOG_FILE_SIZE,
            backupCount=LOG_BACKUP_COUNT
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        _user_loggers[username] = logger
    return _user_loggers[username]


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    username: Optional[str] = payload.get("sub")
    if username is None:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    if token is None:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None


def get_current_user_from_query(
    token: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Optional[User]:
    if token is None:
        return None
    try:
        payload = decode_access_token(token)
        if payload is None:
            return None
        username: Optional[str] = payload.get("sub")
        if username is None:
            return None
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.is_active:
            return None
        return user
    except Exception:
        return None
