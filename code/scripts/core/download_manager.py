import time
import os
import platform
from pathlib import Path
from typing import Optional
import logging

from PySide6.QtCore import QThread, Signal

from utils.path_utils import VIDEOS_DIR

logger = logging.getLogger()


class DownloaderThread(QThread):
    progress = Signal(float, str)   # percent, status message
    done = Signal(str)              # path to downloaded file
    error = Signal(str)

    def __init__(self, url: str, parent=None):
        logger.info(f"Initializing DownloaderThread for URL: {url}")
        super().__init__(parent)
        self.url = url
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure directories exist and are writable on both platforms"""
        logger.debug("Ensuring video directory exists and is writable")
        try:
            VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Video directory ensured: {VIDEOS_DIR}")
            
            # On Linux, ensure proper permissions
            if platform.system() != "Windows":
                try:
                    os.chmod(VIDEOS_DIR, 0o755)
                    logger.debug("Set directory permissions on Linux")
                except Exception as e:
                    logger.warning(f"Could not set directory permissions: {e}")
                    # Permission changes might fail, but that's usually OK
                    
        except Exception as e:
            logger.error(f"Directory setup failed: {e}", exc_info=True)
            self.error.emit(f"Directory setup failed: {e}")

    def run(self):
        logger.info(f"Starting download thread for: {self.url}")
        try:
            import yt_dlp
            logger.debug("yt_dlp imported successfully")
        except Exception as e:
            error_msg = f"yt_dlp missing: {e}. Install with: pip install yt-dlp"
            logger.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
            self.done.emit("")
            return

        try:
            def progress_hook(d):
                try:
                    status = d.get("status")
                    logger.debug(f"Progress hook called with status: {status}")
                    
                    if status == "downloading":
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        downloaded = d.get("downloaded_bytes", 0)
                        percent = 0.0
                        
                        if total:
                            try:
                                percent = float(downloaded) / float(total) * 100.0
                            except Exception:
                                percent = 0.0
                                logger.warning("Failed to calculate percentage from total bytes")
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
                        logger.debug(f"Download progress: {percent:.1f}%, Speed: {speed_str}, ETA: {eta_str}")
                        
                        try:
                            self.progress.emit(percent, status_msg)
                        except Exception as e:
                            logger.error(f"Failed to emit progress signal: {e}")

                    elif status == "finished":
                        logger.info("Download finished, processing...")
                        try:
                            self.progress.emit(100.0, "Processing...")
                        except Exception as e:
                            logger.error(f"Failed to emit finished progress signal: {e}")
                        time.sleep(0.3)
                        
                except Exception as e:
                    logger.error(f"Error in progress hook: {e}", exc_info=True)

            # Enhanced yt-dlp options to handle 403 errors
            outtmpl = os.path.join(str(VIDEOS_DIR), "%(title)s.%(ext)s")
            logger.debug(f"Output template set to: {outtmpl}")

            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                "merge_output_format": "mp4",
                "noplaylist": True,
                "quiet": False,
                "no_warnings": False,
                "ignoreerrors": False,  # Changed to False to catch errors properly
                "progress_hooks": [progress_hook],
                
                # Enhanced options for 403 errors
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-us,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.7",
                    "Connection": "keep-alive",
                    "Referer": "https://www.youtube.com/",
                },
                
                # Retry settings
                "retries": 5,
                "fragment_retries": 5,
                "skip_unavailable_fragments": True,
                "throttledratelimit": 1000000,
                
                # Format selection
                "format_sort": ["res:1080", "res:720", "res:480", "res:360", "mp4", "webm"],
                
                # Additional options for YouTube
                "extract_flat": False,
            }

            logger.info("Starting YouTube download with enhanced yt-dlp options")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    self.progress.emit(0, "Checking video availability...")
                    logger.debug("Extracting video info (no download)")
                    info = ydl.extract_info(self.url, download=False)
                    
                    if not info:
                        error_msg = "Could not extract video information"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    video_title = info.get('title', 'Unknown')
                    video_duration = info.get('duration', 'Unknown')
                    logger.info(f"Video info extracted - Title: '{video_title}', Duration: {video_duration}s")
                    
                    self.progress.emit(0, f"Downloading: {video_title}")
                    logger.info(f"Starting download: {video_title}")
                    
                    # Download the video
                    ydl.download([self.url])
                    logger.info("Download completed successfully")
                    
                except Exception as extract_error:
                    logger.error(f"Download failed: {extract_error}", exc_info=True)
                    raise extract_error

                # Find the downloaded file
                filename = None
                try:
                    filename = ydl.prepare_filename(info) if info else None
                    logger.debug(f"Prepared filename: {filename}")
                except Exception as e:
                    logger.warning(f"Could not prepare filename: {e}")
                    filename = None

                # Look for the downloaded file
                downloaded_file = None
                possible_paths = []
                
                if filename:
                    possible_paths.append(Path(filename))
                    possible_paths.append(Path(filename).with_suffix(".mp4"))
                    possible_paths.append(Path(filename).with_suffix(".mkv"))
                    possible_paths.append(Path(filename).with_suffix(".webm"))
                    logger.debug(f"Generated possible filenames: {[str(p) for p in possible_paths]}")
                
                # Check for recently created files
                try:
                    recent_files = sorted(
                        [p for p in VIDEOS_DIR.iterdir() if p.is_file() and p.stat().st_mtime > time.time() - 300],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    possible_paths.extend(recent_files)
                    logger.debug(f"Added {len(recent_files)} recent files to search")
                except Exception as e:
                    logger.warning(f"Could not check recent files: {e}")
                
                # Find the first existing file
                downloaded_file = next((p for p in possible_paths if p.exists()), None)
                logger.debug(f"Downloaded file found: {downloaded_file}")
                
                if not downloaded_file:
                    error_msg = "Download finished but file not found in videos folder."
                    logger.error(error_msg)
                    raise FileNotFoundError(error_msg)

                file_size = downloaded_file.stat().st_size if downloaded_file else 0
                logger.info(f"Downloaded file confirmed: {downloaded_file.name} ({file_size} bytes)")
                
                if file_size == 0:
                    error_msg = "Downloaded file is empty (0 bytes)."
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                # Success - emit the file path
                self.done.emit(str(downloaded_file.resolve()))
                logger.info("Download completed successfully, emitted done signal")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Download failed: {error_msg}", exc_info=True)
            
            # Enhanced error message handling
            if "403" in error_msg or "Forbidden" in error_msg:
                error_msg = "YouTube blocked the download (HTTP 403). This is usually temporary. Try again later or use a different video."
                logger.warning("YouTube returned 403 Forbidden - likely temporary blocking")
            elif "Private video" in error_msg:
                error_msg = "This is a private YouTube video and cannot be downloaded."
                logger.warning("Attempted to download private video")
            elif "Sign in" in error_msg or "age-restricted" in error_msg.lower():
                error_msg = "This video requires sign-in or may be age-restricted."
                logger.warning("Video requires sign-in or is age-restricted")
            elif "unable to extract" in error_msg.lower():
                error_msg = "Unable to extract video information. The video may not be available or the URL is invalid."
                logger.warning("Could not extract video information")
            elif "FileNotFoundError" in error_msg:
                error_msg = "Download completed but file was not found. The download may have failed."
                logger.warning("Download file not found after completion")
            
            logger.error(f"Final error message: {error_msg}")
            
            self.error.emit(error_msg)
            self.done.emit("")  # Emit empty string to indicate failure