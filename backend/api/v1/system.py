import shutil
import subprocess
import os
import psutil
import threading
import time
import sys
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from backend.core.config import YT_DLP_PATH, DENO_PATH
from backend.core.deps import app_logger
import platform

router = APIRouter(prefix="/system", tags=["system"])


class VersionResponse(BaseModel):
    version: str


class AppInfoResponse(BaseModel):
    title: str
    description: str
    version: str


@router.get("/app-info", response_model=AppInfoResponse)
def get_app_info():
    from backend.main import app
    return {
        "title": app.title,
        "description": app.description,
        "version": app.version
    }


@router.get("/version", response_model=VersionResponse)
def get_version():
    from backend.main import app
    return {"version": app.version}


class SystemCheckResponse(BaseModel):
    yt_dlp_installed: bool
    yt_dlp_version: str
    deno_installed: bool
    deno_version: str


class UpgradeResponse(BaseModel):
    success: bool
    message: str


@router.get("/check", response_model=SystemCheckResponse)
def get_system_check():
    yt_dlp_installed = False
    yt_dlp_version = ""
    
    yt_dlp_path = YT_DLP_PATH
    if yt_dlp_path and not os.path.exists(yt_dlp_path):
        yt_dlp_path = "yt-dlp"
    
    try:
        result = subprocess.run(
            [yt_dlp_path or "yt-dlp", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            yt_dlp_installed = True
            yt_dlp_version = result.stdout.strip()
    except Exception:
        pass
    
    deno_installed = False
    deno_version = ""
    
    deno_path = DENO_PATH
    if deno_path and not os.path.exists(deno_path):
        deno_path = "deno"
    
    try:
        result = subprocess.run(
            [deno_path or "deno", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            deno_installed = True
            deno_version = result.stdout.strip().split('\n')[0]
    except Exception:
        pass
    
    return {
        "yt_dlp_installed": yt_dlp_installed,
        "yt_dlp_version": yt_dlp_version,
        "deno_installed": deno_installed,
        "deno_version": deno_version,
    }


class ServerInfoResponse(BaseModel):
    platform: str
    python_version: str
    cpu_count: int
    memory_total: int
    memory_available: int
    disk_total: int
    disk_used: int
    disk_free: int


class EnvConfigResponse(BaseModel):
    model_config = {"extra": "allow"}


@router.get("/env-config", response_model=EnvConfigResponse)
def get_env_config():
    env_vars = read_env_file()
    
    result = {}
    for key, value in env_vars.items():
        if key.startswith('#') or not key:
            continue
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, int):
            result[key] = value
        elif isinstance(value, str):
            if value.lower() in ('true', 'false'):
                result[key] = value.lower() == 'true'
            elif value.isdigit():
                result[key] = int(value)
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result



@router.get("/server-info", response_model=ServerInfoResponse)
def get_server_info():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_total": memory.total,
        "memory_available": memory.available,
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
    }


def read_env_file():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    env_path = os.path.join(project_root, ".env")
    
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if value.lower() == 'true':
                        env_vars[key] = True
                    elif value.lower() == 'false':
                        env_vars[key] = False
                    elif value.isdigit():
                        env_vars[key] = int(value)
                    else:
                        env_vars[key] = value
    
    return env_vars


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


@router.put("/env-config", response_model=dict)
# TODO: Revisit this endpoint for Docker compatibility - hardcoded path fails in containers
def update_env_config(config: dict):
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    env_path = os.path.join(project_root, ".env")
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        existing_keys = {}
        for line in lines:
            line = line.strip()
            if line and '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                existing_keys[key.strip()] = value.strip()
        
        for key, value in config.items():
            existing_keys[key] = str(value)
        
        with open(env_path, 'w') as f:
            for key, value in existing_keys.items():
                f.write(f"{key}={value}\n")
        
        app_logger.info(f"Environment config updated: {list(config.keys())}")
        return {"success": True, "message": "Configuration updated. Restart server to apply changes."}
    except Exception as e:
        app_logger.error(f"Failed to update env config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart", response_model=dict)
def restart_server():
    trigger_file = os.path.join(os.getcwd(), "backend", "main.py")
    with open(trigger_file, "a"):
        os.utime(trigger_file, None)
    
    app_logger.info(f"Restart triggered via file modification")
    
    return {"success": True, "message": "Server restarting...", "code": "RESTART"}


@router.post("/shutdown", response_model=dict)
def shutdown_server():
    import subprocess
    
    shutdown_flag = os.path.join(os.getcwd(), "backend", ".shutdown_trigger")
    with open(shutdown_flag, "w") as f:
        f.write(str(os.getpid()))
    
    app_logger.info(f"Shutdown triggered via flag file")
    
    current_pid = os.getpid()
    parent_pid = os.getppid()
    
    def kill_all():
        import time
        time.sleep(2)
        
        import subprocess
        subprocess.run(['pkill', '-f', 'uvicorn'], stderr=subprocess.DEVNULL)
        
        time.sleep(1)
        try:
            os.kill(parent_pid, 9)
        except:
            pass
        try:
            os.kill(current_pid, 9)
        except:
            pass
    
    import threading
    thread = threading.Thread(target=kill_all)
    thread.daemon = True
    thread.start()
    
    return {"success": True, "message": "Server shutting down...", "code": "SHUTDOWN"}


@router.post("/upgrade", response_model=UpgradeResponse)
def upgrade_yt_dlp():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            app_logger.info("yt-dlp upgraded successfully")
            return {"success": True, "message": "yt-dlp upgraded successfully"}
        else:
            app_logger.error(f"yt-dlp upgrade failed: {result.stderr}")
            return {"success": False, "message": f"Upgrade failed: {result.stderr}"}

    except Exception as e:
        app_logger.error(f"yt-dlp upgrade error: {str(e)}")
        return {"success": False, "message": str(e)}
