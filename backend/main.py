from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# TODO: Add l10n (internationalization) support using FastAPI's request localization or similar
from backend.db.base import Base
from backend.db.session import engine, SessionLocal
from backend.db.models import User, Config, UrlSource, DownloadedFile, DownloadJob
from backend.api.v1 import auth, configs, urls, downloads, system, logs, files, tasks
from backend.db.sync import sync_all_users
from backend.core.deps import app_logger
from backend.core.config import ADMIN_USERNAME, ADMIN_PASSWORD, BASE_DIR
from backend.core.security import get_password_hash

STATIC_DIR = BASE_DIR / "backend" / "static"

# NOTE: Update app information here before release
app = FastAPI(
    title="yt-dlp Manager",
    description="yt-dlp Manager is a feature-rich download manager for the yt-dlp engine, supporting thousands of websites and offering multi-user capabilities.",
    version="0.0.9"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# TODO: Refactor all endpoints - some endpoints are useless and should be removed or consolidated

app.include_router(auth.router, prefix="/api/v1")
app.include_router(configs.router, prefix="/api/v1")
app.include_router(urls.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")


@app.on_event("startup")
def startup_event():
    app_logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    app_logger.info("Syncing JSON files and downloads to database...")
    sync_all_users()
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not admin:
            admin = User(
                username=ADMIN_USERNAME,
                email=f"{ADMIN_USERNAME}@yt-dlp-manager.local",
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_admin=True
            )
            db.add(admin)
            db.commit()
            app_logger.info(f"Default admin user created: {ADMIN_USERNAME}")
    finally:
        db.close()
    
    from backend.services.scheduler import scheduler
    scheduler.start()
    
    app_logger.info("yt-dlp Manager backend started")


@app.get("/")
def root():
    index_path = STATIC_DIR / "index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": app.title, "version": app.version}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
