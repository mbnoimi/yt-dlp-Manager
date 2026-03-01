import os
import json
import time
import threading
from datetime import datetime
from typing import Optional
from croniter import croniter
from pathlib import Path

from backend.core.deps import app_logger
from backend.db.session import SessionLocal
from backend.db.models import ScheduledTask, User
from backend.services.downloader import start_download_job


class TaskScheduler:
    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._check_interval = 60

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        app_logger.info("Task scheduler started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        app_logger.info("Task scheduler stopped")

    def _run_scheduler(self):
        while self._running:
            try:
                self._check_and_run_tasks()
            except Exception as e:
                app_logger.error(f"Scheduler error: {e}")
            time.sleep(self._check_interval)

    def _check_and_run_tasks(self):
        db = SessionLocal()
        try:
            now = datetime.utcnow()
            tasks = db.query(ScheduledTask).filter(
                ScheduledTask.is_active == True
            ).all()

            for task in tasks:
                if self._should_run_task(task, now):
                    self._run_task(task)
                    task.last_run = now
                    self._update_next_run(task, db)
                    db.commit()
        except Exception as e:
            app_logger.error(f"Error checking tasks: {e}")
        finally:
            db.close()

    def _should_run_task(self, task: ScheduledTask, now: datetime) -> bool:
        if not task.cron_expression:
            return False
        
        try:
            cron = croniter(task.cron_expression, now)
            prev_run = cron.get_prev(datetime)
            if task.last_run:
                return prev_run > task.last_run
            return True
        except Exception:
            return False

    def _run_task(self, task: ScheduledTask):
        app_logger.info(f"Running scheduled task: {task.name} (ID: {task.id}, type: {task.task_type})")
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == task.user_id).first()
            if not user:
                app_logger.error(f"User not found for task {task.id}")
                return

            if task.task_type == "download":
                self._run_download_task(task, user, db)
            elif task.task_type == "cleanup":
                self._run_cleanup_task(task, user)
            else:
                app_logger.error(f"Unknown task type: {task.task_type}")
        except Exception as e:
            app_logger.error(f"Error running task {task.id}: {e}")
        finally:
            db.close()

    def _run_download_task(self, task: ScheduledTask, user: User, db):
        from backend.db.models import Config, UrlSource
        
        config = db.query(Config).filter(
            Config.user_id == task.user_id,
            Config.name == task.datasource
        ).first()
        urls = db.query(UrlSource).filter(
            UrlSource.user_id == task.user_id,
            UrlSource.name == task.datasource
        ).first()

        if not config or not urls:
            app_logger.error(f"Config or URLs not found for datasource {task.datasource}")
            return

        start_download_job(
            username=user.username,
            user_id=user.id,
            config_name=task.datasource,
            urls_name=task.datasource,
            create_symlinks=True
        )
        app_logger.info(f"Started download job for task {task.name}")

    def _run_cleanup_task(self, task: ScheduledTask, user: User):
        config = {}
        if task.config:
            try:
                config = json.loads(task.config)
            except Exception:
                pass
        
        days = config.get("days", 30)
        
        result = delete_old_files(task.user_id, days, user.username)
        app_logger.info(f"Cleanup task {task.name}: deleted {result['files_deleted']} files, {result['folders_deleted']} folders, freed {result['space_freed']} bytes")

    def _update_next_run(self, task: ScheduledTask, db):
        try:
            cron = croniter(task.cron_expression, datetime.utcnow())
            next_run = cron.get_next(datetime)
            task.next_run = next_run
        except Exception:
            task.next_run = None


def validate_cron_expression(cron: str) -> bool:
    try:
        croniter(cron)
        return True
    except Exception:
        return False


def get_next_run_time(cron: str) -> Optional[datetime]:
    try:
        cron_obj = croniter(cron, datetime.utcnow())
        return cron_obj.get_next(datetime)
    except Exception:
        return None


def delete_old_files(user_id: int, days: int, username: str) -> dict:
    """
    Delete files older than specified days from user's downloads folder.
    Returns a dict with count of deleted files and folders.
    """
    # TODO: Modify task parameters by adding "datasource" in addition to "days to keep"
    downloads_path = Path(f"data/{username}/downloads")
    if not downloads_path.exists():
        return {"files_deleted": 0, "folders_deleted": 0, "space_freed": 0}
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    
    files_deleted = 0
    folders_deleted = 0
    space_freed = 0
    
    for root, dirs, files in os.walk(downloads_path, topdown=False):
        root_path = Path(root)
        
        for file in files:
            file_path = root_path / file
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    space_freed += file_path.stat().st_size
                    file_path.unlink()
                    files_deleted += 1
            except Exception as e:
                app_logger.error(f"Error deleting file {file_path}: {e}")
        
        for dir_name in dirs:
            dir_path = root_path / dir_name
            try:
                if dir_path.exists() and not any(dir_path.iterdir()):
                    if dir_path.stat().st_mtime < cutoff_time:
                        dir_path.rmdir()
                        folders_deleted += 1
            except Exception as e:
                app_logger.error(f"Error checking dir {dir_path}: {e}")
    
    for root, dirs, files in os.walk(downloads_path, topdown=False):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            try:
                if dir_path.exists() and not any(dir_path.iterdir()):
                    if dir_path.stat().st_mtime < cutoff_time:
                        dir_path.rmdir()
                        folders_deleted += 1
            except Exception as e:
                app_logger.error(f"Error deleting empty dir {dir_path}: {e}")
    
    app_logger.info(f"Deleted {files_deleted} files and {folders_deleted} folders for user {username}, freed {space_freed} bytes")
    
    return {
        "files_deleted": files_deleted,
        "folders_deleted": folders_deleted,
        "space_freed": space_freed
    }


scheduler = TaskScheduler()
