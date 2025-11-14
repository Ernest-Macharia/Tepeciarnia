import time
import os
import platform
import yt_dlp
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
        """Main download thread with improved error handling"""
        logging.info(f"Starting download thread for URL: {self.url}")
        
        try:
            # Configure yt-dlp with better error handling
            ydl_opts = {
                'outtmpl': str(VIDEOS_DIR / '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'noplaylist': True,
                'continuedl': True,
                'noprogress': True,  # We handle progress ourselves
                'nooverwrites': True,
                'writethumbnail': False,
                'ignoreerrors': False,  # Don't ignore errors
                'socket_timeout': 30,
                'retries': 3,
            }
            
            # Custom progress hook
            def progress_hook(d):
                if d['status'] == 'downloading':
                    if 'total_bytes' in d and d['total_bytes']:
                        percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                        speed = d.get('speed', 0)
                        speed_str = f"{speed / 1024 / 1024:.1f} MB/s" if speed else "Unknown speed"
                        status = f"Downloading... {percent:.1f}% ({speed_str})"
                        self.progress.emit(percent, status)
                    else:
                        status = f"Downloading... {d.get('_percent_str', '0%')}"
                        self.progress.emit(0, status)
                
                elif d['status'] == 'finished':
                    self.progress.emit(100, "Download completed! Processing...")
                    logging.info(f"Download finished: {d.get('filename', 'Unknown')}")
                
                elif d['status'] == 'error':
                    logging.error(f"Download error in progress hook: {d}")
                    self.progress.emit(0, f"Error: {d.get('error', 'Unknown error')}")
            
            ydl_opts['progress_hooks'] = [progress_hook]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logging.info("Starting yt-dlp download")
                self.progress.emit(0, "Starting download...")
                
                # Extract info first to validate
                info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise Exception("Could not extract video information")
                
                logging.info(f"Video info extracted: {info.get('title', 'Unknown')}")
                self.progress.emit(5, f"Preparing: {info.get('title', 'Video')}")
                
                # Start download
                result = ydl.download([self.url])
                logging.info(f"Download process completed with result: {result}")
                
                # Find the actual downloaded file
                downloaded_file = self._find_downloaded_file(info.get('title'))
                if downloaded_file and downloaded_file.exists():
                    self.progress.emit(100, "Download completed successfully!")
                    logging.info(f"Download successful: {downloaded_file}")
                    self.done.emit(str(downloaded_file))
                else:
                    raise Exception("Downloaded file not found after completion")
                    
        except yt_dlp.utils.DownloadError as e:
            error_msg = f"Download failed: {str(e)}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        except yt_dlp.utils.ExtractorError as e:
            error_msg = f"Extraction failed: {str(e)}"
            logging.error(error_msg)
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logging.error(error_msg, exc_info=True)
            self.error.emit(error_msg)
        finally:
            logging.info("Download thread finished")

    def _find_downloaded_file(self, title):
        """Find the actual downloaded file after completion"""
        if not title:
            return None
        
        # Look for files that match the title pattern
        possible_patterns = [
            f"{title}.mp4",
            f"{title}.mkv", 
            f"{title}.webm",
            f"{title}.*"
        ]
        
        for pattern in possible_patterns:
            for file_path in VIDEOS_DIR.glob(pattern):
                if file_path.exists() and file_path.stat().st_size > 0:
                    logging.info(f"Found downloaded file: {file_path}")
                    return file_path
        
        # If no exact match, look for recent files in download directory
        recent_files = sorted(VIDEOS_DIR.glob("*"), key=os.path.getmtime, reverse=True)
        for file_path in recent_files[:5]:  # Check 5 most recent files
            if file_path.exists() and file_path.stat().st_size > 0:
                logging.info(f"Found recent file as download: {file_path}")
                return file_path
        
        logging.warning("No downloaded file found")
        return None