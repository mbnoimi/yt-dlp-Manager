import json
import os
from datetime import datetime
from pathlib import Path
from backend.db.session import SessionLocal
from backend.db.models import User, Config, UrlSource, DownloadedFile


DATA_DIR = Path("data")
GLOBAL_DIR = Path("global")


def get_user_data_dir(username: str) -> Path:
    return DATA_DIR / username


def get_user_configs_dir(username: str) -> Path:
    return get_user_data_dir(username) / "configs"


def get_user_urls_dir(username: str) -> Path:
    return get_user_data_dir(username) / "urls"


def get_user_downloads_dir(username: str) -> Path:
    return get_user_data_dir(username) / "downloads"


def get_user_avatar_dir(username: str) -> Path:
    return get_user_data_dir(username) / "avatar"


def ensure_user_dirs(username: str):
    dirs = [
        get_user_data_dir(username),
        get_user_configs_dir(username),
        get_user_urls_dir(username),
        get_user_downloads_dir(username),
        get_user_avatar_dir(username),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def sync_user_configs(user_id: int, username: str):
    db = SessionLocal()
    try:
        configs_dir = get_user_configs_dir(username)
        if not configs_dir.exists():
            return

        existing_names = set()
        for json_file in configs_dir.glob("*.json"):
            existing_names.add(json_file.stem)
            with open(json_file, "r", encoding="utf-8") as f:
                content = f.read()

            existing = db.query(Config).filter(
                Config.user_id == user_id,
                Config.name == json_file.stem
            ).first()

            if existing:
                if existing.content != content:
                    existing.content = content
                    existing.updated_at = datetime.utcnow()
            else:
                new_config = Config(
                    user_id=user_id,
                    name=json_file.stem,
                    content=content
                )
                db.add(new_config)

        db.query(Config).filter(
            Config.user_id == user_id,
            ~Config.name.in_(existing_names)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def sync_user_urls(user_id: int, username: str):
    db = SessionLocal()
    try:
        urls_dir = get_user_urls_dir(username)
        if not urls_dir.exists():
            return

        existing_names = set()
        for json_file in urls_dir.glob("*.json"):
            existing_names.add(json_file.stem)
            with open(json_file, "r", encoding="utf-8") as f:
                content = f.read()

            existing = db.query(UrlSource).filter(
                UrlSource.user_id == user_id,
                UrlSource.name == json_file.stem
            ).first()

            if existing:
                if existing.content != content:
                    existing.content = content
                    existing.updated_at = datetime.utcnow()
            else:
                new_url = UrlSource(
                    user_id=user_id,
                    name=json_file.stem,
                    content=content
                )
                db.add(new_url)

        db.query(UrlSource).filter(
            UrlSource.user_id == user_id,
            ~UrlSource.name.in_(existing_names)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def sync_user_downloads(user_id: int, username: str):
    db = SessionLocal()
    try:
        downloads_dir = get_user_downloads_dir(username)
        if not downloads_dir.exists():
            return

        existing_paths = set()
        for root, dirs, files in os.walk(downloads_dir):
            rel_dir = os.path.relpath(root, downloads_dir)
            if rel_dir == '.':
                rel_dir = ''
            
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.join(rel_dir, filename) if rel_dir else filename
                existing_paths.add(rel_path)
                
                existing = db.query(DownloadedFile).filter(
                    DownloadedFile.user_id == user_id,
                    DownloadedFile.file_path == rel_path
                ).first()

                if not existing:
                    new_file = DownloadedFile(
                        user_id=user_id,
                        url=f"file://{rel_path}",
                        file_path=rel_path
                    )
                    db.add(new_file)

        db.query(DownloadedFile).filter(
            DownloadedFile.user_id == user_id,
            ~DownloadedFile.file_path.in_(existing_paths)
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()


def sync_all_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            sync_user_configs(user.id, user.username)
            sync_user_urls(user.id, user.username)
            sync_user_downloads(user.id, user.username)
    finally:
        db.close()


def write_config_to_file(username: str, name: str, content: str):
    config_path = get_user_configs_dir(username) / f"{name}.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    return config_path


def write_urls_to_file(username: str, name: str, content: str):
    urls_path = get_user_urls_dir(username) / f"{name}.json"
    urls_path.parent.mkdir(parents=True, exist_ok=True)
    with open(urls_path, "w", encoding="utf-8") as f:
        f.write(content)
    return urls_path


def delete_config_file(username: str, name: str):
    config_path = get_user_configs_dir(username) / f"{name}.json"
    if config_path.exists():
        config_path.unlink()


def delete_urls_file(username: str, name: str):
    urls_path = get_user_urls_dir(username) / f"{name}.json"
    if urls_path.exists():
        urls_path.unlink()


def delete_user_data_folder(username: str):
    user_dir = get_user_data_dir(username)
    if user_dir.exists():
        import shutil
        shutil.rmtree(user_dir)


def rename_user_folder(old_username: str, new_username: str):
    old_dir = get_user_data_dir(old_username)
    new_dir = get_user_data_dir(new_username)
    if old_dir.exists() and not new_dir.exists():
        old_dir.rename(new_dir)


def sync_folders_to_db():
    db = SessionLocal()
    try:
        if not DATA_DIR.exists():
            return []

        created_users = []
        for folder in DATA_DIR.iterdir():
            if folder.is_dir() and folder.name not in ('global', 'logs'):
                username = folder.name
                existing = db.query(User).filter(User.username == username).first()
                if not existing:
                    from backend.core.security import get_password_hash
                    new_user = User(
                        username=username,
                        email=f"{username}@local",
                        hashed_password=get_password_hash("changeme"),
                        is_active=True,
                        is_admin=False
                    )
                    db.add(new_user)
                    created_users.append(username)

        if created_users:
            db.commit()

        return created_users
    finally:
        db.close()
