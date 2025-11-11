import time
import os
import platform
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal

from utils.path_utils import VIDEOS_DIR


class DownloaderThread(QThread):
    progress = Signal(float, str)   # percent, status message
    done = Signal(str)              # path to downloaded file
    error = Signal(str)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self.url = url
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure directories exist and are writable on both platforms"""
        try:
            VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
            
            # On Linux, ensure proper permissions
            if platform.system() != "Windows":
                try:
                    os.chmod(VIDEOS_DIR, 0o755)
                except Exception:
                    pass  # Permission changes might fail, but that's usually OK
                    
        except Exception as e:
            self.error.emit(f"Directory setup failed: {e}")

    def _get_safe_filename(self, filename):
        """Remove invalid characters for both Windows and Linux"""
        # Characters invalid on Windows: < > : " | ? *
        # Characters to avoid on Linux: / and null bytes
        invalid_chars = '<>:"|?*/\0'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename

    def run(self):
        try:
            import yt_dlp
        except Exception as e:
            try:
                self.error.emit(f"yt_dlp missing: {e}. Install with: pip install yt-dlp")
            except Exception:
                pass
            self.done.emit("")
            return

        try:
            def progress_hook(d):
                try:
                    status = d.get("status")
                    if status == "downloading":
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        downloaded = d.get("downloaded_bytes", 0)
                        percent = 0.0
                        if total:
                            try:
                                percent = float(downloaded) / float(total) * 100.0
                            except Exception:
                                percent = 0.0
                        else:
                            percent = d.get("progress", 0.0) or 0.0

                        speed = d.get("speed", 0)
                        if speed:
                            if speed > 1024*1024:
                                speed_str = f"{speed/1024/1024:.1f} MB/s"
                            elif speed > 1024:
                                speed_str = f"{speed/1024:.1f} KB/s"
                            else:
                                speed_str = f"{speed:.1f} B/s"
                        else:
                            speed_str = "unknown"

                        eta = d.get("eta", 0)
                        if eta and eta > 0:
                            if eta >= 3600:
                                eta_str = f"{int(eta//3600)}h {int((eta%3600)//60)}m"
                            elif eta >= 60:
                                eta_str = f"{int(eta//60)}m {int(eta%60)}s"
                            else:
                                eta_str = f"{int(eta)}s"
                        else:
                            eta_str = "unknown"

                        status_msg = f"Downloading... {percent:.1f}% ({speed_str}, ETA: {eta_str})"
                        try:
                            self.progress.emit(percent, status_msg)
                        except Exception:
                            pass

                    elif status == "finished":
                        try:
                            self.progress.emit(100.0, "Processing...")
                        except Exception:
                            pass
                        time.sleep(0.3)
                except Exception:
                    pass

            # Cross-platform path handling
            outtmpl = os.path.join(str(VIDEOS_DIR), "%(title)s.%(ext)s")

            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": False,
                "no_warnings": False,
                "ignoreerrors": True,
                "progress_hooks": [progress_hook],
                
                # Cross-platform compatible options
                "extract_flat": False,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-us,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                    "Connection": "keep-alive",
                },
                
                "retries": 10,
                "fragment_retries": 10,
                "skip_unavailable_fragments": True,
                "throttledratelimit": 1000000,
                "format_sort": ["res:1080", "res:720", "res:480", "res:360", "mp4", "webm"],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    self.progress.emit(0, "Checking video availability...")
                    info = ydl.extract_info(self.url, download=False)
                    
                    if not info:
                        raise Exception("Could not extract video information")
                    
                    video_title = info.get('title', 'Unknown')
                    self.progress.emit(0, f"Downloading: {video_title}")
                    
                    ydl.download([self.url])
                    
                except Exception as extract_error:
                    self.progress.emit(0, "Trying alternative download method...")
                    info = ydl.extract_info(self.url, download=True)

                # Cross-platform file detection
                filename = None
                try:
                    filename = ydl.prepare_filename(info) if info else None
                except Exception:
                    filename = None

                possible = []
                if filename:
                    possible.append(Path(filename))
                    possible.append(Path(filename).with_suffix(".mp4"))
                    possible.append(Path(filename).with_suffix(".mkv"))
                    possible.append(Path(filename).with_suffix(".webm"))
                
                # Check for recently created files (works on both platforms)
                try:
                    recent_files = sorted(
                        [p for p in VIDEOS_DIR.iterdir() if p.is_file() and p.stat().st_mtime > time.time() - 300],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    possible.extend(recent_files)
                except Exception:
                    pass
                
                existing = next((p for p in possible if p.exists()), None)
                
                if not existing:
                    try:
                        all_files = sorted(
                            [p for p in VIDEOS_DIR.iterdir() if p.is_file()],
                            key=lambda x: x.stat().st_mtime,
                            reverse=True
                        )
                        existing = all_files[0] if all_files else None
                    except Exception:
                        existing = None

                if not existing:
                    raise FileNotFoundError("Download finished but file not found in videos folder.")

                try:
                    self.done.emit(str(existing.resolve()))
                except Exception:
                    try:
                        self.done.emit(str(existing))
                    except Exception:
                        self.done.emit("")

        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                error_msg = "YouTube blocked the download (HTTP 403). This video may have restrictions or yt-dlp needs updating."
            elif "Private video" in error_msg:
                error_msg = "This is a private YouTube video and cannot be downloaded."
            elif "Sign in" in error_msg:
                error_msg = "This video requires sign-in or may be age-restricted."
            
            try:
                self.error.emit(error_msg)
            except Exception:
                pass
            try:
                self.done.emit("")
            except Exception:
                pass