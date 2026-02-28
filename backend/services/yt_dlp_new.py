#!/usr/bin/env python3
"""
yt-dlp-new.py - Enhanced yt-dlp wrapper using yt-dlp as a Python library

Features:
- Uses yt_dlp library instead of subprocess
- Auto-upgrade yt-dlp before downloading
- Random user agents and sleep durations to bypass rate limiting
- Accepts all yt-dlp default arguments (forward-compatible)
- Custom arguments for batch downloading from JSON files
- All yt-dlp arguments come from JSON file (fully dynamic)
"""

import logging
import random
import time
import json
import os
import sys
import shutil
import threading
from datetime import datetime

def get_logger(name: str = "yt-dlp-new") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

log = get_logger()

def timestamped_print(*args, **kwargs):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}]", *args, **kwargs)
import subprocess
from datetime import datetime
from typing import Dict, List, Union, Optional, Tuple, Any, Callable
from queue import Queue, Empty

try:
    import yt_dlp
except ImportError:
    print("yt-dlp library not installed. Install with: pip install yt-dlp")
    sys.exit(1)


DEFAULT_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
]


def upgrade_yt_dlp() -> bool:
    """Upgrades yt-dlp to the latest version using multiple methods."""
    upgrade_methods = [
        ["pipx", "upgrade", "yt-dlp"],
        ["pip", "install", "--upgrade", "yt-dlp"],
        ["pip3", "install", "--upgrade", "yt-dlp"],
        ["python", "-m", "pip", "install", "--upgrade", "yt-dlp"],
        ["python3", "-m", "pip", "install", "--upgrade", "yt-dlp"],
    ]
    
    for method in upgrade_methods:
        try:
            print(f"Attempting upgrade with: {' '.join(method)}", flush=True)
            result = subprocess.run(method, capture_output=True, text=True)
            if result.returncode == 0:
                print("yt-dlp upgraded successfully.", flush=True)
                return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Upgrade method failed: {' '.join(method)} - {e}", flush=True)
            continue

    print("All upgrade methods failed. Continuing with current version...", flush=True)
    return False


def get_random_user_agent() -> str:
    """Returns a random user agent string."""
    return random.choice(DEFAULT_USER_AGENTS)


def parse_range_value(value: Any) -> Union[float, int, str]:
    """
    Parse a range value like '5-15' and return a random value within that range.
    If it's a single number, return it as-is.
    """
    if isinstance(value, (int, float)):
        return value
    
    if '-' in str(value):
        parts = str(value).split('-')
        try:
            min_val = float(parts[0])
            max_val = float(parts[1])
            if min_val == int(min_val) and max_val == int(max_val):
                return random.randint(int(min_val), int(max_val))
            return random.uniform(min_val, max_val)
        except (ValueError, IndexError):
            pass
    
    try:
        return float(value)
    except ValueError:
        return value


def build_yt_dlp_opts_from_json(args_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a JSON args dictionary to yt-dlp options dict."""
    ytdlp_opts = {}
    
    # Handle new format: separate yt-dlp and custom sections
    if "yt-dlp" in args_dict:
        yt_dlp_section = args_dict.get("yt-dlp", {})
        custom_section = args_dict.get("custom", {})
        
        for key, value in yt_dlp_section.items():
            opt_key = key.lstrip('-').replace('-', '_')
            
            if isinstance(value, bool):
                if value:
                    ytdlp_opts[opt_key] = True
                continue
            
            if isinstance(value, str) and ',' in value:
                if opt_key in ('sub_langs', 'subtitles', 'languages', 'sub_lang', 'subtitleslangs'):
                    ytdlp_opts[opt_key] = [v.strip() for v in value.split(',')]
                    if opt_key == 'sub_langs':
                        ytdlp_opts['subtitleslangs'] = ytdlp_opts.pop('sub_langs')
                    if opt_key == 'subtitleslangs':
                        ytdlp_opts['writesubtitles'] = True
                        ytdlp_opts['writeautomaticsub'] = True
                    continue
            
            parsed_value = parse_range_value(value)
            ytdlp_opts[opt_key] = parsed_value
        
        return ytdlp_opts, custom_section
    
    # Handle legacy format
    for key, value in args_dict.items():
        if key.startswith('_'):
            continue
        
        opt_key = key.lstrip('-').replace('-', '_')
        
        if isinstance(value, bool):
            if value:
                ytdlp_opts[opt_key] = True
            continue
        
        if isinstance(value, str) and ',' in value:
            if opt_key in ('sub_langs', 'subtitles', 'languages', 'sub_lang', 'subtitleslangs'):
                ytdlp_opts[opt_key] = [v.strip() for v in value.split(',')]
                if opt_key == 'sub_langs':
                    ytdlp_opts['subtitleslangs'] = ytdlp_opts.pop('sub_langs')
                if opt_key == 'subtitleslangs':
                    ytdlp_opts['writesubtitles'] = True
                    ytdlp_opts['writeautomaticsub'] = True
            continue
        
        if isinstance(value, list):
            ytdlp_opts[opt_key] = value
            continue
        
        parsed_value = parse_range_value(value)
        ytdlp_opts[opt_key] = parsed_value
    
    return ytdlp_opts, {}


def load_urls_from_json(urls_file: str) -> Dict[str, List[str]]:
    """Load URLs from a JSON file."""
    with open(urls_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    result = {}
    for folder, urls in data.items():
        if isinstance(urls, str):
            result[folder] = [urls]
        elif isinstance(urls, list):
            result[folder] = urls
        else:
            print(f"Warning: Invalid URL format for folder '{folder}': {urls}")
    
    return result


class DownloadState:
    def __init__(self, timeout: int, stall_timeout: int, log_callback: Optional[Callable] = None):
        self.timeout = timeout
        self.stall_timeout = stall_timeout
        self.log_callback = log_callback
        self.start_time = time.time()
        self.last_progress_time = time.time()
        self.stalled = False
        self.timed_out = False
        self._lock = threading.Lock()
    
    def check_progress(self, status: str, info: Dict = None):
        with self._lock:
            current_time = time.time()
            
            if current_time - self.start_time > self.timeout:
                self.timed_out = True
                msg = f"\n[TIMEOUT] Download exceeded {self.timeout}s"
                print(msg, flush=True)
                if self.log_callback:
                    self.log_callback(msg, False)
                return False
            
            if status == 'downloading' or (info and info.get('status') == 'downloading'):
                self.last_progress_time = current_time
            
            elapsed_since_progress = current_time - self.last_progress_time
            if elapsed_since_progress > self.stall_timeout and not self.stalled:
                self.stalled = True
                msg = f"\n[STALL] No progress for {elapsed_since_progress:.0f}s"
                print(msg, flush=True)
                if self.log_callback:
                    self.log_callback(msg, False)
                return False
            
            return True
    
    def log(self, msg: str, is_err: bool = False):
        print(msg, flush=True)
        if self.log_callback:
            self.log_callback(msg, is_err)


def run_yt_dlp(
    url: str,
    ytdlp_opts: Dict[str, Any],
    output_template: Optional[str] = None,
    timeout: int = 7200,
    stall_timeout: int = 300,
    use_random_agent: bool = True,
    log_callback: Optional[Callable[[str, bool], None]] = None,
) -> Tuple[int, str, str]:
    """
    Run yt-dlp with the given options using the library.
    Returns (returncode, info_json, error_message).
    """
    opts = ytdlp_opts.copy()
    
    opts['quiet'] = False
    opts['verbose'] = True
    
    # Don't fail on subtitle download errors (e.g., 429 rate limiting)
    # These should not prevent the video download from succeeding
    opts['ignoreerrors'] = True
    opts['no_warnings'] = False
    
    # Disable subtitles if they cause too many issues - can be enabled in config
    # Check if subtitles are explicitly enabled in opts
    if not opts.get('writesubtitles') and not opts.get('write_auto_subs'):
        # Subtitles not requested, don't change anything
        pass
    
    if use_random_agent:
        opts['http_headers'] = {'User-Agent': get_random_user_agent()}
    
    if output_template:
        opts['outtmpl'] = output_template
    
    state = DownloadState(timeout, stall_timeout, log_callback)
    info_json_str = ""
    
    def progress_hook(d):
        status = d.get('status', '')
        
        if status == 'downloading':
            if not state.check_progress(status, d):
                raise Exception("Download stalled or timed out")
        
        if status == 'finished':
            state.log(f"  [finished] {d.get('filename', 'unknown')}")
        
        if status == 'error':
            state.log(f"  [error] {d.get('error', 'unknown error')}", True)
    
    opts['progress_hooks'] = [progress_hook]
    
    # Filter to suppress verbose/unimportant yt-dlp messages
    def filter_log(msg: str) -> bool:
        suppress_patterns = [
            "Extracting URL:",
            "Downloading webpage",
            "player response playability status",
            "Forcing",
            "original url =",
            "android_vr player response",
            "web player response",
            "web_safari player response",
            "Downloading android vr player",
            "Downloading web safari player",
            "Downloading tv html5 player",
            "Downloading player",
            "[debug] ",
            "Redownloading playlist API JSON",
            "Downloading API JSON",
            "Downloading playlist:",
            "page 1: Downloading",
            "Downloading item",
            "Playlist ",
            "The information of all playlist entries",
            "PO Token Providers:",
            "PO Token Cache Providers:",
            "PO Token Cache Spec Providers:",
            "JS Challenge Providers:",
            "No title found in player responses",
            "encodings:",
            "exe versions:",
            "Optional libraries:",
            "JS runtimes:",
            "Proxy map:",
            "Request Handlers:",
            "Plugin directories:",
            "Loaded ",
            "Loading archive file",
            "params:",
            "Python ",
        ]
        for pattern in suppress_patterns:
            if pattern.lower() in msg.lower():
                return True
        return False
    
    class Logger:
        def __init__(self, log_func):
            self.log_func = log_func
        def debug(self, msg):
            if not filter_log(msg):
                self.log_func(f"[yt-dlp] {msg}")
        def warning(self, msg):
            self.log_func(f"[yt-dlp] {msg}")
        def error(self, msg):
            self.log_func(f"[yt-dlp] {msg}")
        def info(self, msg):
            if not filter_log(msg):
                self.log_func(f"[yt-dlp] {msg}")
    
    opts['logger'] = Logger(state.log)
    
    try:
        state.log(f"Starting download: {url}")
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            info_json_str = json.dumps(ydl.sanitize_info(info))
            
            if opts.get('write_info_json') and info:
                final_filename = ydl.prepare_filename(info)
                info_json_path = os.path.splitext(final_filename)[0] + '.info.json'
                with open(info_json_path, 'w', encoding='utf-8') as f:
                    json.dump(ydl.sanitize_info(info), f, ensure_ascii=False, indent=2)
                state.log(f"Wrote info.json: {info_json_path}")
            
            if opts.get('write_thumbnail') and info:
                final_filename = ydl.prepare_filename(info)
                thumb_path = os.path.splitext(final_filename)[0] + '.webp'
                if not os.path.exists(thumb_path) and 'thumbnail' in info:
                    thumb_url = info.get('thumbnail')
                    if thumb_url:
                        try:
                            import urllib.request
                            urllib.request.urlretrieve(thumb_url, thumb_path)
                            state.log(f"Wrote thumbnail: {thumb_path}")
                        except Exception as e:
                            state.log(f"Failed to write thumbnail: {e}")
            
            if opts.get('write_description') and info:
                final_filename = ydl.prepare_filename(info)
                desc_path = os.path.splitext(final_filename)[0] + '.description'
                if 'description' in info and info['description']:
                    try:
                        with open(desc_path, 'w', encoding='utf-8') as f:
                            f.write(info['description'])
                        state.log(f"Wrote description: {desc_path}")
                    except Exception as e:
                        state.log(f"Failed to write description: {e}")
            
            if opts.get('write_link') and info:
                final_filename = ydl.prepare_filename(info)
                link_path = os.path.splitext(final_filename)[0] + '.link'
                if 'url' in info:
                    try:
                        with open(link_path, 'w', encoding='utf-8') as f:
                            f.write(info['url'])
                        state.log(f"Wrote link: {link_path}")
                    except Exception as e:
                        state.log(f"Failed to write link: {e}")
            
            if opts.get('download_archive') and info:
                archive_path = opts.get('download_archive')
                if 'id' in info and 'extractor' in info:
                    try:
                        yt_id = info.get('id')
                        archive_line = f"{info['extractor']} {yt_id}\n"
                        # Check for duplicates before writing
                        if archive_path and os.path.exists(archive_path):
                            with open(archive_path, 'r', encoding='utf-8') as f:
                                existing = f.read()
                            if archive_line.strip() in existing:
                                state.log(f"Archive entry already exists: {archive_line.strip()}")
                            else:
                                with open(archive_path, 'a', encoding='utf-8') as f:
                                    f.write(archive_line)
                                state.log(f"Wrote archive: {archive_line.strip()}")
                        else:
                            with open(archive_path, 'a', encoding='utf-8') as f:
                                f.write(archive_line)
                            state.log(f"Wrote archive: {archive_line.strip()}")
                    except Exception as e:
                        state.log(f"Failed to write archive: {e}")
        
        state.log("Download completed successfully")
        return 0, info_json_str, ""
    
    except Exception as e:
        error_msg = str(e)
        
        if state.timed_out:
            return -1, "", f"Timeout after {timeout} seconds"
        
        if state.stalled:
            return -1, "", f"Download stalled (no progress for {stall_timeout}s)"
        
        # Check if video was downloaded despite the error
        # This handles cases like subtitle 429 errors where video downloads fine
        if output_template:
            import glob
            video_pattern = output_template.replace('%(ext)s', '*')
            downloaded_files = glob.glob(video_pattern)
            video_files = [f for f in downloaded_files if f.endswith(('.mp4', '.mkv', '.webm', '.flv'))]
            if video_files:
                state.log(f"Video file found despite error: {video_files[0]}")
                state.log("Download completed successfully (with errors)")
                return 0, info_json_str, ""
        
        return -1, "", error_msg


def ensure_poster(folder_path: str, log_callback: Optional[Callable[[str, bool], None]] = None) -> bool:
    """
    Ensure a poster image exists in the folder.
    """
    def log(msg: str, is_err: bool = False):
        if log_callback:
            log_callback(msg, is_err)
        print(msg, flush=True)
    
    log(f"[poster] Checking folder: {folder_path}")
    
    image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg')
    
    if not os.path.isdir(folder_path):
        log(f"[poster] Folder does not exist: {folder_path}")
        return False
    
    try:
        files = os.listdir(folder_path)
    except OSError as e:
        log(f"[poster] Error listing folder: {e}")
        return False
    
    poster_exists = any(
        f.lower().startswith('poster.') and f.lower().endswith(image_exts)
        for f in files
    )
    
    if poster_exists:
        return False
    
    na_file = None
    first_image = None
    folder_image = None
    
    for f in files:
        file_path = os.path.join(folder_path, f)
        if not os.path.isfile(file_path):
            continue
        
        f_lower = f.lower()
        
        if not f_lower.endswith(image_exts):
            continue
        
        if first_image is None:
            first_image = f
        
        if f_lower.startswith('folder.'):
            folder_image = f
            break
        
        if f.startswith('NA - ') and f_lower.endswith(image_exts):
            na_file = f
    
    if folder_image:
        ext = os.path.splitext(folder_image)[1]
        target = os.path.join(folder_path, f'poster{ext}')
        try:
            shutil.copy2(os.path.join(folder_path, folder_image), target)
            log(f"  [poster] Copied folder image to poster{ext}")
            return True
        except OSError as e:
            log(f"  [poster] Error copying folder image: {e}")
            return False
    
    if na_file:
        target = os.path.join(folder_path, 'poster.jpg')
        try:
            os.rename(os.path.join(folder_path, na_file), target)
            log(f"  [poster] Renamed '{na_file}' to poster.jpg")
            return True
        except OSError as e:
            log(f"  [poster] Error renaming NA file: {e}")
            return False
    
    if first_image:
        ext = os.path.splitext(first_image)[1]
        target = os.path.join(folder_path, f'poster{ext}')
        try:
            shutil.copy2(os.path.join(folder_path, first_image), target)
            log(f"  [poster] Copied '{first_image}' to poster{ext}")
            return True
        except OSError as e:
            log(f"  [poster] Error copying first image: {e}")
            return False
    
    log(f"[poster] No images found in folder")
    return False


def download_batch(
    urls_dict: Dict[str, List[str]],
    base_path: str,
    base_args: Dict[str, Any],
    max_videos: int = 0,
    max_duration: int = 0,
    ensure_posters: bool = False,
    use_random_agent: bool = True,
    download_timeout: int = 7200,
    stall_timeout: int = 300,
    log_callback: Optional[Callable[[str, bool], None]] = None,
    stop_check_callback: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Download videos from a dictionary of URLs using args from JSON."""
    stats = {
        'start_time': datetime.now().isoformat(),
        'videos_downloaded': 0,
        'errors': 0,
        'skipped': 0,
        'folders_processed': 0,
        'total_urls': 0,
        'timeouts': 0,
        'stalls': 0,
    }
    
    session_start = time.time()
    videos_downloaded = 0
    
    for folder_name, urls in urls_dict.items():
        if stop_check_callback and stop_check_callback():
            timestamped_print("Stop requested, exiting folder loop")
            break
        
        if max_duration > 0 and (time.time() - session_start) >= max_duration:
            timestamped_print(f"Reached maximum session duration ({max_duration/3600:.1f} hours)")
            break
        
        if max_videos > 0 and videos_downloaded >= max_videos:
            timestamped_print(f"Reached maximum videos ({max_videos})")
            break
        
        folder_path = os.path.join(base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        output_template = os.path.join(folder_path, "%(upload_date)s - %(title)s.%(ext)s")
        
        timestamped_print(f"\n{'='*60}")
        timestamped_print(f"Processing folder: {folder_name}")
        timestamped_print(f"URLs to process: {len(urls)}")
        timestamped_print(f"{'='*60}")
        
        for i, url in enumerate(urls):
            if stop_check_callback and stop_check_callback():
                timestamped_print("Stop requested, exiting download loop")
                break
            
            if max_videos > 0 and videos_downloaded >= max_videos:
                break
            if max_duration > 0 and (time.time() - session_start) >= max_duration:
                break
            
            timestamped_print(f"\n[{i+1}/{len(urls)}] Downloading: {url}")
            
            ytdlp_opts = base_args.copy()
            
            if max_videos > 0:
                remaining = max_videos - videos_downloaded
                if remaining > 0:
                    ytdlp_opts['max_downloads'] = remaining
            
            returncode, info_json, stderr = run_yt_dlp(
                url=url,
                ytdlp_opts=ytdlp_opts,
                output_template=output_template,
                use_random_agent=use_random_agent,
                timeout=download_timeout,
                stall_timeout=stall_timeout,
                log_callback=log_callback,
            )
            
            if returncode == -1:
                if "Timeout" in stderr or "timeout" in stderr:
                    stats['timeouts'] += 1
                    timestamped_print(f"  Download timed out after {download_timeout}s")
                elif "stalled" in stderr.lower():
                    stats['stalls'] += 1
                    timestamped_print(f"  Download stalled (no progress for {stall_timeout}s)")
                stats['errors'] += 1
                error_msg = stderr[:200] if stderr else "Unknown error"
                timestamped_print(f"  Error: {error_msg}")
                if log_callback:
                    log_callback(f"  Error: {error_msg}", True)
                
                sleep_time = random.uniform(30, 60)
                timestamped_print(f"  Sleeping {sleep_time:.1f}s before next URL...")
                time.sleep(sleep_time)
                continue
            
            if returncode == 0:
                videos_downloaded += 1
                stats['videos_downloaded'] += 1
                timestamped_print(f"  Downloaded: 1")
                if log_callback:
                    log_callback("  Downloaded: 1", False)
            else:
                stats['errors'] += 1
                error_msg = stderr[:200] if stderr else "Unknown error"
                timestamped_print(f"  Error: {error_msg}")
                if log_callback:
                    log_callback(f"  Error: {error_msg}", True)
                
                if "rate-limit" in stderr.lower() or "429" in stderr:
                    sleep_time = random.uniform(600, 1200)
                    timestamped_print(f"  Rate limited! Sleeping {sleep_time/60:.1f} minutes")
                    if log_callback:
                        log_callback(f"  Rate limited! Sleeping {sleep_time/60:.1f} minutes", True)
                    time.sleep(sleep_time)
            
            if i < len(urls) - 1:
                if stop_check_callback and stop_check_callback():
                    timestamped_print("Stop requested, exiting download loop")
                    break
                    
                if folder_name:
                    sleep_time = random.uniform(10, 30)
                else:
                    sleep_time = random.uniform(2, 5)
                timestamped_print(f"  Sleeping {sleep_time:.1f}s before next URL...")
                time.sleep(sleep_time)
        
        stats['folders_processed'] += 1
        stats['total_urls'] += len(urls)
        
        if ensure_posters:
            ensure_poster(folder_path, log_callback)
        
        if folder_name:
            sleep_time = random.uniform(30, 60)
            timestamped_print(f"\nCompleted folder: {folder_name}. Sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
    
    stats['end_time'] = datetime.now().isoformat()
    stats['duration_seconds'] = time.time() - session_start
    
    return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Enhanced yt-dlp wrapper using yt-dlp library with rate limiting protection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Custom Arguments:
  --urls FILE          JSON file with folder names as keys and URLs as values
  --path PATH          Base path where sub-folders and files will be saved
  --upgrade            Upgrade yt-dlp before starting download process
  --args FILE          JSON file containing yt-dlp arguments
  --random-agent       Enable random user agent rotation for each download
  --download-timeout   Max time per video download in seconds (default: 7200)
  --stall-timeout      Max time without progress before stall (default: 300)

All yt-dlp arguments (format, cookies, download_archive, etc.)
should be specified in the JSON args file.

Examples:
  %(prog)s --urls docs.json --path /downloads --args my-args.json --upgrade
  %(prog)s --urls urls.json --path /videos --args args.json
  %(prog)s --urls urls.json --path /videos --download-timeout 3600 --stall-timeout 180
        """
    )
    
    parser.add_argument("--urls", type=str, help="JSON file with folder names as keys and URLs as values")
    parser.add_argument("--path", type=str, help="Base path where sub-folders and files will be saved")
    parser.add_argument("--upgrade", action="store_true", help="Upgrade yt-dlp before starting download process")
    parser.add_argument("--args", type=str, help="JSON file containing yt-dlp arguments")
    parser.add_argument("--max-videos", type=int, default=0, help="Maximum videos to download (0 = unlimited)")
    parser.add_argument("--max-duration", type=int, default=0, help="Maximum session duration in seconds (0 = unlimited)")
    parser.add_argument("--download-timeout", type=int, default=7200, help="Maximum time per video download in seconds")
    parser.add_argument("--stall-timeout", type=int, default=300, help="Maximum time without progress before stall")
    parser.add_argument("--poster", action="store_true", help="Ensure poster image exists in each folder")
    parser.add_argument("--random-agent", action="store_true", help="Enable random user agent rotation")
    
    args, remaining_args = parser.parse_known_args()
    
    if args.upgrade:
        upgrade_yt_dlp()
    
    base_args = {}
    if args.args:
        if os.path.exists(args.args):
            print(f"Loading arguments from {args.args}", flush=True)
            with open(args.args, 'r', encoding='utf-8') as f:
                args_dict = json.load(f)
            base_args, custom = build_yt_dlp_opts_from_json(args_dict)
            print(f"Loaded {len(base_args)} arguments from JSON", flush=True)
        else:
            print(f"Warning: Args file not found: {args.args}", flush=True)
    
    use_random_agent = args.random_agent
    
    if args.urls:
        if not args.path:
            print("Error: --path is required when using --urls", flush=True)
            sys.exit(1)

        if not os.path.exists(args.urls):
            print(f"Error: URLs file not found: {args.urls}", flush=True)
            sys.exit(1)

        print(f"Loading URLs from {args.urls}", flush=True)
        urls_dict = load_urls_from_json(args.urls)
        print(f"Loaded {len(urls_dict)} folders", flush=True)
        
        os.makedirs(args.path, exist_ok=True)
        
        stats = download_batch(
            urls_dict=urls_dict,
            base_path=args.path,
            base_args=base_args,
            max_videos=args.max_videos,
            max_duration=args.max_duration,
            ensure_posters=args.poster,
            use_random_agent=use_random_agent,
            download_timeout=args.download_timeout,
            stall_timeout=args.stall_timeout
        )
        
        print(f"\n{'='*60}", flush=True)
        print("DOWNLOAD SUMMARY", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Videos downloaded: {stats['videos_downloaded']}", flush=True)
        print(f"Videos skipped: {stats['skipped']}", flush=True)
        print(f"Errors: {stats['errors']}", flush=True)
        print(f"Timeouts: {stats.get('timeouts', 0)}", flush=True)
        print(f"Stalled: {stats.get('stalls', 0)}", flush=True)
        print(f"Folders processed: {stats['folders_processed']}", flush=True)
        print(f"Total URLs: {stats['total_urls']}", flush=True)
        print(f"Duration: {stats['duration_seconds']/60:.1f} minutes", flush=True)
        print(f"{'='*60}", flush=True)

    else:
        print("No --urls provided, use as library or provide URLs file", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
