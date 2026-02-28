from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models import User
from backend.db.sync import ensure_user_dirs, sync_user_configs, sync_user_urls, delete_user_data_folder, sync_folders_to_db
from backend.core.security import verify_password, get_password_hash, create_access_token
from backend.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, get_allow_only_one_admin, get_admin_username, get_allow_new_users
from backend.core.deps import get_current_user, app_logger, get_user_logger

router = APIRouter(prefix="/auth", tags=["auth"])


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar: Optional[str] = None
    is_active: bool
    is_admin: bool = False

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class UsernameChange(BaseModel):
    new_username: str


class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if not get_allow_new_users():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="New user registration is disabled"
        )
    
    if user.username.lower() == "global":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username 'global' is reserved"
        )
    
    existing = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    is_first_user = False
    if get_allow_only_one_admin():
        existing_admin = db.query(User).filter(User.is_admin == True).first()
        is_first_user = existing_admin is None

    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=is_first_user
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    ensure_user_dirs(db_user.username)
    user_logger = get_user_logger(db_user.username)
    user_logger.info(f"New user registered")
    app_logger.info(f"New user registered: {db_user.username}")

    return db_user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    user_logger = get_user_logger(user.username)
    user_logger.info(f"User logged in")
    app_logger.info(f"User logged in: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin users cannot delete their own account"
        )
    username = current_user.username
    user_logger = get_user_logger(username)
    user_logger.info(f"User deleted account")
    db.delete(current_user)
    db.commit()
    delete_user_data_folder(username)
    app_logger.info(f"User deleted: {username}")
    return None


@router.post("/me/password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    user_logger = get_user_logger(current_user.username)
    user_logger.info(f"Password changed")
    app_logger.info(f"User {current_user.username} changed password")
    
    return {"message": "Password changed successfully"}


@router.put("/me/username", status_code=status.HTTP_200_OK)
def change_username(
    username_data: UsernameChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_username = username_data.new_username
    
    if new_username.lower() == "global":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username 'global' is reserved"
        )
    
    existing = db.query(User).filter(User.username == new_username).first()
    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    old_username = current_user.username
    current_user.username = new_username
    db.commit()
    
    from backend.db.sync import rename_user_folder
    rename_user_folder(old_username, new_username)
    
    user_logger = get_user_logger(new_username)
    user_logger.info(f"Username changed from {old_username}")
    app_logger.info(f"User {old_username} changed username to {new_username}")
    
    return {"message": "Username changed successfully", "username": new_username}


class EmailChange(BaseModel):
    new_email: EmailStr


@router.put("/me/email", response_model=UserResponse)
def change_email(
    email_data: EmailChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    new_email = email_data.new_email
    
    existing = db.query(User).filter(User.email == new_email, User.id != current_user.id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already taken"
        )
    
    old_email = current_user.email
    current_user.email = new_email
    db.commit()
    
    user_logger = get_user_logger(current_user.username)
    user_logger.info(f"Email changed from {old_email}")
    app_logger.info(f"User {current_user.username} changed email from {old_email} to {new_email}")
    
    return current_user


class AvatarUpdate(BaseModel):
    avatar: str


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from backend.core.config import BASE_DIR
    import io
    from PIL import Image
    
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed")
    
    ensure_user_dirs(current_user.username)
    avatar_dir = BASE_DIR / "data" / current_user.username / "avatar"
    avatar_dir.mkdir(parents=True, exist_ok=True)
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    
    img = Image.open(io.BytesIO(contents))
    
    if img.width > 512 or img.height > 512:
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
    
    avatar_path = avatar_dir / "avatar.png"
    img.save(avatar_path, "PNG")
    
    avatar_url = f"/api/v1/avatar/{current_user.username}/avatar.png"
    current_user.avatar = avatar_url
    db.commit()
    
    return current_user


@router.put("/me/avatar", response_model=UserResponse)
def update_avatar_url(
    avatar_data: AvatarUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.avatar = avatar_data.avatar
    db.commit()
    return current_user


@router.post("/users/sync", response_model=list[UserResponse])
def sync_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    created = sync_folders_to_db()
    if created:
        app_logger.info(f"Synced folders to DB: {created}")
    
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    if user_data.username.lower() == "global":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username 'global' is reserved"
        )
    
    existing = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_admin=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    ensure_user_dirs(db_user.username)
    app_logger.info(f"User {db_user.username} created by admin {current_user.username}")
    
    return db_user


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    users = db.query(User).all()
    return users


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    if user.username.lower() == get_admin_username().lower():
        raise HTTPException(status_code=400, detail="Cannot delete the super admin")
    
    username = user.username
    db.delete(user)
    db.commit()
    delete_user_data_folder(username)
    app_logger.info(f"User {username} deleted by admin {current_user.username}")
    
    return None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_admin: Optional[bool] = None


class UserPasswordChange(BaseModel):
    new_password: str


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user_data.username:
        if user_data.username.lower() == "global":
            raise HTTPException(status_code=400, detail="Username 'global' is reserved")
        existing = db.query(User).filter(User.username == user_data.username, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = user_data.username
    
    if user_data.email:
        existing = db.query(User).filter(User.email == user_data.email, User.id != user_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already taken")
        user.email = user_data.email
    
    if user_data.is_admin is not None:
        if user.username.lower() == get_admin_username().lower():
            raise HTTPException(status_code=400, detail="Cannot modify super admin's permissions")
        if user_data.is_admin:
            if get_allow_only_one_admin():
                existing_admin = db.query(User).filter(User.is_admin == True, User.id != user_id).first()
                if existing_admin:
                    raise HTTPException(status_code=400, detail="Another user is already an admin")
        user.is_admin = user_data.is_admin
    
    db.commit()
    db.refresh(user)
    app_logger.info(f"User {user.id} updated by admin {current_user.username}")
    
    return user


@router.post("/users/{user_id}/password", status_code=status.HTTP_200_OK)
def change_user_password(
    user_id: int,
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    app_logger.info(f"Password for user {user.username} changed by admin {current_user.username}")
    
    return {"message": "Password changed successfully"}
