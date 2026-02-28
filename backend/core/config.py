import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

GLOBAL_DIR = DATA_DIR / "global"
GLOBAL_DIR.mkdir(exist_ok=True)

BACKEND_DIR = BASE_DIR / "backend"
LOGS_DIR = BACKEND_DIR / "logs"
SCRIPT_DIR = BASE_DIR / "script"

DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{DATA_DIR.absolute()}/yt-dlp_manager.db"

SECRET_KEY = os.getenv("BACKEND_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
PORT = int(os.getenv("BACKEND_PORT", "8200"))

YT_DLP_PATH = os.getenv("YT_DLP_PATH", "yt-dlp")
DENO_PATH = os.getenv("DENO_PATH", "deno")

MAX_LOG_FILE_SIZE = int(os.getenv("MAX_LOG_FILE_SIZE", "10240")) * 1024
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

MAX_COOKIES_FILE_SIZE = int(os.getenv("MAX_COOKIES_FILE_SIZE", "10")) * 1024 * 1024  # 10 MB default

MAX_CONCURRENT_DOWNLOADS = int(os.getenv("BACKEND_MAX_CONCURRENT_DOWNLOADS", "3"))
DEDUPLICATION_ENABLED = os.getenv("BACKEND_DEDUPLICATION_ENABLED", "true").lower() == "true"

def get_allow_only_one_admin():
    return os.getenv("ALLOW_ONLY_ONE_ADMIN", "true").lower() == "true"

def get_allow_new_users():
    return os.getenv("ALLOW_NEW_USERS", "false").lower() == "true"

ALLOW_ONLY_ONE_ADMIN = get_allow_only_one_admin()

def get_admin_username():
    return os.getenv("ADMIN_USERNAME", "admin")

ADMIN_USERNAME = get_admin_username()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "pass")
