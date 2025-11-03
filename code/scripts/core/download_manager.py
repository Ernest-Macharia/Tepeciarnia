import time
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

    def run(self):
        try:
            import yt_dlp
        except Exception as e:
            try:
                self.error.emit(f"yt_dlp missing: {e}")
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

            outtmpl = str(VIDEOS_DIR / "%(title)s.%(ext)s")

            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "noplaylist": False,
                "quiet": True,
                "no_warnings": True,
                "ignoreerrors": False,
                "progress_hooks": [progress_hook],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=True)

                filename = None
                try:
                    filename = ydl.prepare_filename(info)
                except Exception:
                    filename = None

                possible = []
                if filename:
                    possible.append(Path(filename))
                    possible.append(Path(filename).with_suffix(".mp4"))
                    possible.append(Path(filename).with_suffix(".mkv"))
                    possible.append(Path(filename).with_suffix(".webm"))
                
                existing = next((p for p in possible if p.exists()), None)
                if not existing:
                    try:
                        candidates = sorted(
                            [p for p in VIDEOS_DIR.iterdir() if p.is_file()],
                            key=lambda x: x.stat().st_mtime,
                            reverse=True
                        )
                        existing = candidates[0] if candidates else None
                    except Exception as e:
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
            try:
                self.error.emit(str(e))
            except Exception:
                pass
            try:
                self.done.emit("")
            except Exception:
                pass