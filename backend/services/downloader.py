import json
import hashlib
import os
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.core.config import BASE_DIR, DATA_DIR, GLOBAL_DIR, SCRIPT_DIR, YT_DLP_PATH, DENO_PATH, MAX_CONCURRENT_DOWNLOADS, DEDUPLICATION_ENABLED
from backend.db.session import SessionLocal
from backend.db.models import DownloadedFile, DownloadJob, Config, UrlSource
from backend.core.deps import get_user_logger
from backend.services.yt_dlp_new import download_batch, build_yt_dlp_opts_from_json


_running_jobs: Dict[int, dict] = {}
_jobs_lock = threading.Lock()

_running_users: set = set()
_users_lock = threading.Lock()

_queue_processing = False
_queue_lock = threading.Lock()

_url_locks: Dict[str, threading.Lock] = {}
_url_locks_lock = threading.Lock()


def get_url_lock(url: str) -> threading.Lock:
    """Get or create a lock for a specific URL."""
    with _url_locks_lock:
        if url not in _url_locks:
            _url_locks[url] = threading.Lock()
        return _url_locks[url]


def acquire_url_lock(url: str, timeout: int = 10) -> bool:
    """Try to acquire a lock for the URL. Returns True if acquired."""
    lock = get_url_lock(url)
    return lock.acquire(timeout=timeout)


def release_url_lock(url: str):
    """Release the lock for the URL."""
    with _url_locks_lock:
        if url in _url_locks:
            try:
                _url_locks[url].release()
            except RuntimeError:
                pass


def hash_url(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def get_global_download_dir(url: str) -> Path:
    url_hash = hash_url(url)
    return GLOBAL_DIR / "downloads" / url_hash


def get_user_download_dir(username: str, folder_name: str) -> Path:
    return DATA_DIR / username / "downloads" / folder_name


def find_existing_file(url: str) -> Optional[str]:
    db = SessionLocal()
    try:
        downloaded = db.query(DownloadedFile).filter(DownloadedFile.url == url).first()
        if downloaded and os.path.exists(downloaded.file_path):
            return downloaded.file_path
        return None
    finally:
        db.close()


def parse_archive_file(archive_path: str, base_url: str) -> List[str]:
    """Parse yt-dlp archive file and extract video IDs."""
    video_ids = []
    yt_video_id_pattern = re.compile(r'youtube[:\s]+([a-zA-Z0-9_-]{11})')
    
    try:
        with open(archive_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                match = yt_video_id_pattern.search(line)
                if match:
                    video_id = match.group(1)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_ids.append(video_url)
    except FileNotFoundError:
        pass
    
    return video_ids


def extract_video_urls_from_output(stdout: str) -> List[str]:
    """Extract individual video URLs from yt-dlp stdout output."""
    video_urls = []
    yt_video_id_pattern = re.compile(r'yt-dlp_manager(?:\:video)?[\s]+([a-zA-Z0-9_-]{11})')
    
    for line in stdout.split('\n'):
        match = yt_video_id_pattern.search(line)
        if match:
            video_id = match.group(1)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            if video_url not in video_urls:
                video_urls.append(video_url)
    
    return video_urls


def sync_all_archives_to_db(db):
    """Sync ALL users' archive files to database for cross-user deduplication."""
    from backend.db.models import User
    
    users = db.query(User).all()
    
    for user in users:
        user_data_dir = DATA_DIR / user.username
        archive_file = user_data_dir / "ytdl-archive.txt"
        
        if archive_file.exists():
            try:
                with open(archive_file, 'r', encoding='utf-8') as f:
                    yt_video_id_pattern = re.compile(r'yt-dlp_manager[:\s]+([a-zA-Z0-9_-]{11})')
                    
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        
                        match = yt_video_id_pattern.search(line)
                        if match:
                            video_id = match.group(1)
                            video_url = f"https://www.youtube.com/watch?v={video_id}"
                            
                            existing = db.query(DownloadedFile).filter(
                                DownloadedFile.url == video_url
                            ).first()
                            
                            if not existing:
                                downloaded = DownloadedFile(
                                    url=video_url,
                                    file_path="",
                                    user_id=user.id
                                )
                                db.add(downloaded)
            except Exception:
                pass
    
    db.commit()


def populate_user_archive(username: str, db):
    """Populate user's archive file with all known video IDs from database for yt-dlp to skip."""
    import re
    
    user_data_dir = DATA_DIR / username
    archive_file = user_data_dir / "ytdl-archive.txt"
    
    existing_ids = set()
    if archive_file.exists():
        try:
            with open(archive_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        existing_ids.add(line)
        except Exception:
            pass
    
    all_videos = db.query(DownloadedFile).all()
    
    yt_id_pattern = re.compile(r'(?:v=|/)([a-zA-Z0-9_-]{11})')
    
    with open(archive_file, 'a', encoding='utf-8') as f:
        for video in all_videos:
            match = yt_id_pattern.search(video.url)
            if match:
                video_id = match.group(1)
                archive_line = f"yt-dlp_manager {video_id}"
                if archive_line not in existing_ids:
                    f.write(archive_line + "\n")


def sync_archive_to_db(archive_path: str, playlist_url: str, user_id: int, db):
    """Sync archive file to database for playlist deduplication."""
    video_urls = parse_archive_file(archive_path, playlist_url)
    
    for video_url in video_urls:
        existing = db.query(DownloadedFile).filter(
            DownloadedFile.url == video_url
        ).first()
        
        if not existing:
            downloaded = DownloadedFile(
                url=video_url,
                file_path="",
                user_id=user_id
            )
            db.add(downloaded)


def add_to_archive(archive_path: str, url: str):
    """Add a URL to the yt-dlp archive file."""
    try:
        import re
        yt_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', url)
        if yt_id_match:
            yt_id = yt_id_match.group(1)
            archive_line = f"yt-dlp_manager {yt_id}\n"
            
            # Check for duplicates before writing
            if os.path.exists(archive_path):
                with open(archive_path, 'r', encoding='utf-8') as f:
                    existing = f.read()
                if archive_line.strip() in existing:
                    return  # Already exists
            
            with open(archive_path, 'a', encoding='utf-8') as f:
                f.write(archive_line)
    except Exception:
        pass


def get_global_file_path(url: str, filename: str) -> Path:
    url_hash = hash_url(url)
    return GLOBAL_DIR / "downloads" / url_hash / filename


def move_to_global(url: str, source_path: Path) -> Optional[Path]:
    try:
        url_hash = hash_url(url)
        global_folder = GLOBAL_DIR / "downloads" / url_hash
        os.makedirs(global_folder, exist_ok=True)
        
        target_path = global_folder / source_path.name
        shutil.move(str(source_path), str(target_path))
        
        if source_path.with_suffix('.info.json').exists():
            shutil.move(
                str(source_path.with_suffix('.info.json')),
                str(target_path.with_suffix('.info.json'))
            )
        if source_path.with_suffix('.jpg').exists():
            shutil.move(
                str(source_path.with_suffix('.jpg')),
                str(target_path.with_suffix('.jpg'))
            )
        if source_path.with_suffix('.png').exists():
            shutil.move(
                str(source_path.with_suffix('.png')),
                str(target_path.with_suffix('.png'))
            )
        if source_path.with_suffix('.webp').exists():
            shutil.move(
                str(source_path.with_suffix('.webp')),
                str(target_path.with_suffix('.webp'))
            )
            
        return target_path
    except Exception:
        return None


def create_symlink(original_path: str, target_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        if os.path.exists(target_path):
            if os.path.islink(target_path):
                os.unlink(target_path)
            else:
                os.remove(target_path)
        os.symlink(original_path, target_path)
        return True
    except Exception:
        return False


def build_yt_dlp_args(config_content: str) -> tuple[List[str], List[str]]:
    """
    Parse config JSON and return tuple of (yt-dlp args, custom script args).
    
    New format:
    {
      "yt-dlp": { "--format": "best", ... },
      "custom": { "--poster": true, "--random-agent": true, ... }
    }
    
    Old format (backwards compatible):
    { "--format": "best", "_poster": true, ... }
    """
    config = json.loads(config_content)
    
    yt_dlp_args = []
    custom_args = []
    
    if "yt-dlp" in config:
        yt_dlp_section = config["yt-dlp"]
        for key, value in yt_dlp_section.items():
            if isinstance(value, bool):
                if value:
                    yt_dlp_args.append(key)
            elif isinstance(value, list):
                yt_dlp_args.append(key)
                yt_dlp_args.append(",".join(str(v) for v in value))
            else:
                yt_dlp_args.append(key)
                yt_dlp_args.append(str(value))
        
        if "custom" in config:
            custom_section = config["custom"]
            for key, value in custom_section.items():
                if isinstance(value, bool):
                    if value:
                        custom_args.append(key)
                elif isinstance(value, list):
                    custom_args.append(key)
                    custom_args.extend(str(v) for v in value)
                else:
                    custom_args.append(key)
                    custom_args.append(str(value))
    else:
        for key, value in config.items():
            if key.startswith("_"):
                if isinstance(value, bool):
                    if value:
                        custom_args.append(key[1:])
                elif isinstance(value, list):
                    custom_args.append(key[1:])
                    custom_args.extend(str(v) for v in value)
                else:
                    custom_args.append(key[1:])
                    custom_args.append(str(value))
            else:
                if isinstance(value, bool):
                    if value:
                        yt_dlp_args.append(key)
                elif isinstance(value, list):
                    yt_dlp_args.append(key)
                    yt_dlp_args.append(",".join(str(v) for v in value))
                else:
                    yt_dlp_args.append(key)
                    yt_dlp_args.append(str(value))
    
    return yt_dlp_args, custom_args


def run_download(
    username: str,
    config_name: str,
    urls_name: str,
    job_id: int,
    create_symlinks: bool = True
):
    db = SessionLocal()
    user_logger = get_user_logger(username)
    
    try:
        job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
        if not job:
            return

        job.status = "running"
        db.commit()
        
        if DEDUPLICATION_ENABLED:
            sync_all_archives_to_db(db)
            populate_user_archive(username, db)
        
        with _jobs_lock:
            _running_jobs[job_id] = {"username": username, "process": None}
        
        user_logger.info(f"Starting download job {job_id}: {config_name}/{urls_name}")

        config = db.query(Config).filter(
            Config.user_id == job.user_id,
            Config.name == config_name
        ).first()

        urls_source = db.query(UrlSource).filter(
            UrlSource.user_id == job.user_id,
            UrlSource.name == urls_name
        ).first()

        if not config or not urls_source:
            job.status = "failed"
            job.error_message = "Config or URLs not found"
            db.commit()
            return

        urls_data = json.loads(urls_source.content)

        for folder_name, urls in urls_data.items():
            with _jobs_lock:
                job_info = _running_jobs.get(job_id, {})
                if job_info.get("stopped"):
                    user_logger.info(f"Job {job_id} was stopped, exiting")
                    break

            if isinstance(urls, str):
                urls = [urls]

            user_folder = get_user_download_dir(username, folder_name)
            os.makedirs(user_folder, exist_ok=True)

            for url in urls:
                with _jobs_lock:
                    job_info = _running_jobs.get(job_id, {})
                    if job_info.get("stopped"):
                        user_logger.info(f"Job {job_id} was stopped, exiting")
                        break

                url_lock_acquired = False
                # FIXME: Deduplication is unstable and may cause issues - use with caution
                use_deduplication = DEDUPLICATION_ENABLED
                
                archive_file_path = None
                config_data = json.loads(config.content)
                
                yt_dlp_config = config_data
                custom_args = []
                
                if "yt-dlp" in config_data:
                    yt_dlp_config = config_data.get("yt-dlp", {})
                    custom_section = config_data.get("custom", {})
                    for key, value in custom_section.items():
                        if isinstance(value, bool):
                            if value:
                                custom_args.append(key)
                        elif isinstance(value, list):
                            custom_args.append(key)
                            custom_args.extend(str(v) for v in value)
                        else:
                            custom_args.append(key)
                            custom_args.append(str(value))
                else:
                    yt_dlp_config = {}
                    for key, value in config_data.items():
                        if key.startswith("_"):
                            custom_key = key[1:]
                            if isinstance(value, bool):
                                if value:
                                    custom_args.append(custom_key)
                            elif isinstance(value, list):
                                custom_args.append(custom_key)
                                custom_args.extend(str(v) for v in value)
                            else:
                                custom_args.append(custom_key)
                                custom_args.append(str(value))
                        else:
                            yt_dlp_config[key] = value
                
                if "download_archive" in yt_dlp_config or "download-archive" in yt_dlp_config or "--download-archive" in yt_dlp_config:
                    if "download_archive" in yt_dlp_config:
                        archive_path = yt_dlp_config["download_archive"]
                    elif "download-archive" in yt_dlp_config:
                        archive_path = yt_dlp_config["download-archive"]
                    else:
                        archive_path = yt_dlp_config["--download-archive"]
                    if not os.path.isabs(archive_path):
                        yt_dlp_config["download_archive"] = str(user_folder.parent / archive_path)
                    
                    user_configs_dir = DATA_DIR / username / "configs"
                    user_configs_dir.mkdir(parents=True, exist_ok=True)
                    
                    archive_file = user_configs_dir / "ytdl-archive.txt"
                    archive_file.touch()
                    yt_dlp_config["download_archive"] = str(archive_file)
                    archive_file_path = str(archive_file)
                    user_logger.info(f"Archive file: {archive_file_path}")
                    
                    if DEDUPLICATION_ENABLED:
                        sync_archive_to_db(archive_file_path, url, job.user_id, db)
                
                if use_deduplication:
                    url_lock_acquired = acquire_url_lock(url, timeout=30)
                    
                    if url_lock_acquired:
                        existing_file = find_existing_file(url)
                        if existing_file:
                            global_path = Path(existing_file)
                            target_file = user_folder / global_path.name
                            if create_symlink(existing_file, str(target_file)):
                                user_logger.info(f"Created symlink (dedup): {global_path.name}")
                                if archive_file_path:
                                    add_to_archive(archive_file_path, url)
                            release_url_lock(url)
                            continue
                    else:
                        existing_file = find_existing_file(url)
                        if existing_file:
                            global_path = Path(existing_file)
                            target_file = user_folder / global_path.name
                            if create_symlink(existing_file, str(target_file)):
                                user_logger.info(f"Created symlink (dedup): {global_path.name}")
                                if archive_file_path:
                                    add_to_archive(archive_file_path, url)
                            continue
                        else:
                            user_logger.warning(f"URL {url} is being downloaded by another job, waiting...")
                            time.sleep(10)
                            url_lock_acquired = acquire_url_lock(url, timeout=60)
                            if url_lock_acquired:
                                existing_file = find_existing_file(url)
                                if existing_file:
                                    global_path = Path(existing_file)
                                    target_file = user_folder / global_path.name
                                    if create_symlink(existing_file, str(target_file)):
                                        user_logger.info(f"Created symlink (dedup): {global_path.name}")
                                        if archive_file_path:
                                            add_to_archive(archive_file_path, url)
                                    release_url_lock(url)
                                    continue

                output_template = str(user_folder / "%(upload_date)s - %(title)s.%(ext)s")

                yt_dlp_config["--output"] = output_template
                
                if "cookies" in yt_dlp_config or "--cookies" in yt_dlp_config:
                    if "cookies" in yt_dlp_config:
                        cookies_path = yt_dlp_config["cookies"]
                    else:
                        cookies_path = yt_dlp_config["--cookies"]
                    user_cookies_path = DATA_DIR / username / "configs" / "cookies.txt"
                    if user_cookies_path.exists():
                        yt_dlp_config["cookies"] = str(user_cookies_path)
                    elif not os.path.isabs(cookies_path):
                        yt_dlp_config["cookies"] = str(SCRIPT_DIR / cookies_path)

                if "download_archive" in yt_dlp_config or "--download-archive" in yt_dlp_config:
                    if "download_archive" in yt_dlp_config:
                        archive_path = yt_dlp_config["download_archive"]
                    else:
                        archive_path = yt_dlp_config["--download-archive"]
                    user_archive_path = DATA_DIR / username / "configs" / "ytdl-archive.txt"
                    if user_archive_path.exists():
                        yt_dlp_config["download_archive"] = str(user_archive_path)
                    elif not os.path.isabs(archive_path):
                        yt_dlp_config["download_archive"] = str(SCRIPT_DIR / archive_path)

                base_args, custom_section = build_yt_dlp_opts_from_json(yt_dlp_config)
                
                urls_data = {"": [url]}
                
                if isinstance(custom_section, dict):
                    ensure_posters = custom_section.get("--poster", False)
                    use_random_agent = custom_section.get("--random-agent", False)
                    download_timeout = custom_section.get("--download-timeout", 7200)
                    stall_timeout = custom_section.get("--stall-timeout", 300)
                else:
                    ensure_posters = False
                    use_random_agent = False
                    download_timeout = 7200
                    stall_timeout = 300
                
                user_logger.info(f"Starting download using library: {url}")
                
                def log_handler(line: str, is_stderr: bool):
                    if is_stderr:
                        user_logger.warning(f"[yt-dlp] {line.rstrip()}")
                    else:
                        user_logger.info(f"[yt-dlp] {line.rstrip()}")
                
                try:
                    with _jobs_lock:
                        existing_info = _running_jobs.get(job_id, {})
                        was_stopped = existing_info.get("stopped", False)
                        if was_stopped:
                            user_logger.info(f"Job {job_id} was stopped, exiting")
                            break
                        _running_jobs[job_id] = {"username": username, "process": None, "stopped": was_stopped, "current_url": url, "logs": []}
                    
                    def stop_check_callback() -> bool:
                        with _jobs_lock:
                            job_info = _running_jobs.get(job_id, {})
                            stopped = job_info.get("stopped", False)
                            print(f"[DEBUG stop_check_callback] job_id={job_id}, stopped={stopped}, job_info={job_info}")
                            return stopped
                    
                    stats = download_batch(
                        urls_dict=urls_data,
                        base_path=str(user_folder),
                        base_args=base_args,
                        ensure_posters=ensure_posters,
                        use_random_agent=use_random_agent,
                        download_timeout=download_timeout,
                        stall_timeout=stall_timeout,
                        log_callback=log_handler,
                        stop_check_callback=stop_check_callback,
                    )
                    
                    with _jobs_lock:
                        job_info = _running_jobs.get(job_id, {})
                        if job_info.get("stopped"):
                            user_logger.info(f"Job {job_id} was stopped after download_batch")
                            break
                    
                    # Check if video files exist regardless of return code
                    # (yt-dlp may return error due to subtitle 429 but video still downloaded)
                    video_check_files = list(user_folder.glob("*.mkv")) + list(user_folder.glob("*.mp4")) + list(user_folder.glob("*.webm")) + list(user_folder.glob("*.flv"))
                    if video_check_files:
                        proc_returncode = 0
                        user_logger.info(f"Video file found, treating as success despite yt-dlp error")
                    elif stats['videos_downloaded'] > 0 or stats['skipped'] > 0:
                        proc_returncode = 0
                    else:
                        proc_returncode = 1
                except Exception as e:
                    # Check if video files exist despite the exception
                    video_check_files = list(user_folder.glob("*.mkv")) + list(user_folder.glob("*.mp4")) + list(user_folder.glob("*.webm")) + list(user_folder.glob("*.flv"))
                    if video_check_files:
                        user_logger.warning(f"Download error but video exists: {str(e)[:100]}")
                        proc_returncode = 0
                    else:
                        user_logger.error(f"Download error for {url}: {str(e)}")
                        proc_returncode = 1
                
                def find_files_following_symlinks(folder, pattern):
                    """Find files matching pattern, following symlinks."""
                    files = []
                    for root, dirs, filenames in os.walk(folder, followlinks=True):
                        for fname in filenames:
                            if fname.lower().endswith(tuple(pattern)):
                                files.append(Path(root) / fname)
                    return files
                
                if proc_returncode == 0:
                    video_files = []
                    image_files = []
                    for file in user_folder.rglob("*.mkv"):
                        if file.is_file():
                            video_files.append(file)
                    for file in user_folder.rglob("*.mp4"):
                        if file.is_file():
                            video_files.append(file)
                    for file in user_folder.rglob("*.webm"):
                        if file.is_file():
                            video_files.append(file)
                    for file in user_folder.rglob("*.flv"):
                        if file.is_file():
                            video_files.append(file)
                    
                    image_files = find_files_following_symlinks(str(user_folder), ['.jpg', '.jpeg', '.webp'])
                    
                    for file in video_files:
                        is_first_download = find_existing_file(url) is None
                        
                        if DEDUPLICATION_ENABLED and is_first_download and create_symlinks:
                            global_path = move_to_global(url, file)
                            if global_path:
                                target_file = user_folder / global_path.name
                                create_symlink(str(global_path), str(target_file))
                                file_path = str(global_path)
                                user_logger.info(f"Moved to global: {global_path.name}")
                                
                                video_stem = global_path.stem
                                video_dir = global_path.parent
                                for ext in ['.jpg', '.jpeg', '.webp', '.png', '.description', '.info.json', '.desktop', '.srt', '.vtt', '.ass']:
                                    related_file = video_dir / f"{video_stem}{ext}"
                                    if related_file.exists():
                                        target_related = user_folder / f"{video_stem}{ext}"
                                        if not target_related.exists():
                                            create_symlink(str(related_file), str(target_related))
                            else:
                                file_path = str(file)
                        else:
                            file_path = str(file)
                        
                        downloaded = DownloadedFile(
                            url=url,
                            file_path=file_path,
                            user_id=job.user_id
                        )
                        db.add(downloaded)
                        db.commit()
                        user_logger.info(f"Downloaded: {os.path.basename(file_path)}")
                    
                    # FIXME: Poster creation for deduplicated files - may not work correctly
                    # when video is symlinked to global folder (video_files won't contain images)
                    if ensure_posters:
                        for video_file in video_files:
                            try:
                                if video_file.is_symlink():
                                    real_video_path = video_file.resolve()
                                else:
                                    real_video_path = video_file
                                
                                video_dir = real_video_path.parent
                                video_stem = real_video_path.stem
                                
                                for ext in ['.jpg', '.jpeg', '.webp', '.png']:
                                    jpg_path = video_dir / f"{video_stem}{ext}"
                                    if jpg_path.exists():
                                        poster_name = f"poster{ext}"
                                        poster_path = user_folder / poster_name
                                        
                                        if not poster_path.exists():
                                            import shutil
                                            shutil.copy2(str(jpg_path), str(poster_path))
                                            user_logger.info(f"Created poster: {poster_name}")
                                        break
                            except Exception as e:
                                user_logger.warning(f"Failed to create poster: {e}")
                    
                    if archive_file_path and DEDUPLICATION_ENABLED:
                        sync_archive_to_db(archive_file_path, url, job.user_id, db)
                else:
                    user_logger.error(f"Download failed")

                if url_lock_acquired:
                    release_url_lock(url)

        with _jobs_lock:
            job_info = _running_jobs.get(job_id, {})
            was_stopped = job_info.get("stopped", False)

        if was_stopped:
            job.status = "failed"
            job.error_message = "Stopped by user"
            job.finished_at = datetime.utcnow()
            db.commit()
            user_logger.info(f"Download job {job_id} was stopped")
        else:
            job.status = "completed"
            job.finished_at = datetime.utcnow()
            db.commit()
            user_logger.info(f"Download job {job_id} completed")

    except Exception as e:
        job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        user_logger.error(f"Download job {job_id} failed: {str(e)}")
    finally:
        with _jobs_lock:
            job_info = _running_jobs.pop(job_id, {})
        
        was_stopped = job_info.get("stopped", False)
        
        if was_stopped:
            job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
            if job and job.status == "running":
                job.status = "failed"
                job.error_message = "Stopped by user"
                job.finished_at = datetime.utcnow()
                db.commit()
                user_logger.info(f"Download job {job_id} was stopped (finally block)")
        
        with _users_lock:
            _running_users.discard(username)
        
        db.close()
        
        process_queue()


def start_download_job(
    username: str,
    user_id: int,
    config_name: str,
    urls_name: str,
    create_symlinks: bool = True
) -> int:
    db = SessionLocal()
    try:
        job = DownloadJob(
            user_id=user_id,
            name=f"{config_name}/{urls_name}",
            status="pending",
            create_symlinks=create_symlinks
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        process_queue()
        return job.id
    finally:
        db.close()


def process_queue():
    global _queue_processing
    
    with _queue_lock:
        if _queue_processing:
            return
        _queue_processing = True

    try:
        while True:
            db = SessionLocal()
            try:
                global_running = db.query(DownloadJob).filter(DownloadJob.status == "running").count()
                if global_running >= MAX_CONCURRENT_DOWNLOADS:
                    break

                next_job = db.query(DownloadJob).filter(
                    DownloadJob.status == "pending"
                ).order_by(DownloadJob.id).first()
                
                if not next_job:
                    break

                from backend.db.models import User
                user = db.query(User).filter(User.id == next_job.user_id).first()
                if not user:
                    next_job.status = "failed"
                    next_job.error_message = "User not found"
                    db.commit()
                    continue

                username = user.username

                with _users_lock:
                    if username in _running_users:
                        break
                    _running_users.add(username)

                next_job.status = "running"
                next_job.started_at = datetime.utcnow()
                db.commit()

                thread = threading.Thread(
                    target=run_download,
                    args=(
                        username,
                        next_job.name.split("/")[0] if "/" in next_job.name else next_job.name,
                        next_job.name.split("/")[1] if "/" in next_job.name else next_job.name,
                        next_job.id,
                        next_job.create_symlinks
                    )
                )
                thread.start()
            finally:
                db.close()
    finally:
        with _queue_lock:
            _queue_processing = False


def stop_download_job(job_id: int) -> bool:
    db = SessionLocal()
    try:
        job = db.query(DownloadJob).filter(DownloadJob.id == job_id).first()
        if not job:
            return False

        username = None
        with _jobs_lock:
            job_info = _running_jobs.get(job_id)
            print(f"[DEBUG stop_download_job] job_id={job_id}, job_info={job_info}")
            if job_info:
                job_info["stopped"] = True
                print(f"[DEBUG stop_download_job] Set stopped=True for job {job_id}")
                proc = job_info.get("process")
                if proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                username = job_info.get("username")
            else:
                print(f"[DEBUG stop_download_job] Job {job_id} not in _running_jobs, marking as failed in DB")
                job.status = "failed"
                job.error_message = "Stopped by user (job not in memory after restart)"
                job.finished_at = datetime.utcnow()
                db.commit()
                return True

        if not username and job.status == "pending":
            job.status = "failed"
            job.error_message = "Stopped by user"
            db.commit()
            username = job.user_id

        if username:
            if isinstance(username, int):
                from backend.db.models import User
                user = db.query(User).filter(User.id == username).first()
                if user:
                    username = user.username
            if username:
                with _users_lock:
                    _running_users.discard(username)

        return True
    finally:
        db.close()


def get_running_jobs(user_id: Optional[int] = None) -> List[dict]:
    db = SessionLocal()
    try:
        running = db.query(DownloadJob).filter(DownloadJob.status == "running").all()
        result = []
        for job in running:
            if user_id is None or job.user_id == user_id:
                job_info = _running_jobs.get(job.id, {})
                result.append({
                    "id": job.id,
                    "name": job.name,
                    "user_id": job.user_id,
                    "started_at": job.started_at,
                    "create_symlinks": job.create_symlinks,
                    "current_url": job_info.get("current_url"),
                })
        return result
    finally:
        db.close()


def get_queue_count() -> int:
    db = SessionLocal()
    try:
        return db.query(DownloadJob).filter(DownloadJob.status == "pending").count()
    finally:
        db.close()
