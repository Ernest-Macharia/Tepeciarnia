# code/scripts/mp4wall.py
# (Save this file as code/scripts/mp4wall.py - replace existing)

"""
mp4wall.py
Unified, cross-platform version implementing:
 - tapeciarnia: URI parsing (CLI)
 - single input field (images & videos + local files)
 - drag & drop
 - downloads via yt_dlp (with progress dialog and temp marker)
 - streaming via mpv when available
 - image fade cross-fade transition
 - system tray (Show / Hide / Exit)
 - autopause subprocess start/stop
 - scheduler (local folder or playlist)
 - favorites / normal download folders (under ~/Pictures/Tapeciarnia)
"""

from __future__ import annotations
import os
import sys
import json
import shutil
import subprocess
import locale
import re
import platform
import time
import random
from pathlib import Path
from typing import Optional

# PySide6 imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, QSystemTrayIcon, QMenu, QWidget,
    QDialog, QVBoxLayout, QLabel, QProgressBar
)
# QAction in some installs triggers import issues; import from QtGui to be safe
from PySide6.QtGui import QAction, QIcon, QPixmap, QDragEnterEvent, QDropEvent, QPainter
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve, Property

# Make sure this file can import ui.mainUI (your generated UI)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "")))
try:
    from ui.mainUI import Ui_MainWindow
except Exception as e:
    raise ImportError("Failed to import ui.mainUI - ensure code/scripts/ui/mainUI.py exists and is importable.") from e

# -------------------------
# Paths & config
# -------------------------

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent.parent
CONFIG_PATH = ROOT_DIR / "config.json"

# ────────────────────────────────
# Cross-platform default downloads folder
# ────────────────────────────────
def get_collections_folder() -> Path:
    """Return the main collection folder for all wallpapers"""
    home = Path.home()
    
    # Always use Pictures/Tapeciarnia for organized structure
    collection_dir = home / "Pictures" / "Tapeciarnia"
    
    # Ensure the directory exists
    collection_dir.mkdir(parents=True, exist_ok=True)
    
    return collection_dir

COLLECTION_DIR = get_collections_folder()
VIDEOS_DIR = COLLECTION_DIR / "Videos"
IMAGES_DIR = COLLECTION_DIR / "Images" 
FAVS_DIR = COLLECTION_DIR / "Favorites"

# Ensure folders exist
for d in (COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR):
    d.mkdir(parents=True, exist_ok=True)
    print(f"DEBUG: Created/verified folder: {d}")

# Temporary download marker (will be moved to appropriate folder later)
TMP_DOWNLOAD_FILE = COLLECTION_DIR / "download_path.tmp"

# ────────────────────────────────
# Other supporting paths
# ────────────────────────────────
TRANSLATIONS_DIR = BASE_DIR / "translations"

# Config file init
if not CONFIG_PATH.exists():
    CONFIG_PATH.write_text(json.dumps({}), encoding="utf-8")


# -------------------------
# Helpers
# -------------------------
def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


def is_image_url_or_path(s: str) -> bool:
    s = s.lower()
    return bool(re.search(r"\.(jpe?g|png|bmp|gif)$", s)) or (s.startswith("http") and bool(re.search(r"\.(jpe?g|png|bmp|gif)(\?.*)?$", s)))


def is_video_url_or_path(s: str) -> bool:
    s = s.lower()
    return bool(re.search(r"\.(mp4|mkv|webm|avi|mov)$", s)) or (s.startswith("http") and bool(re.search(r"\.(mp4|mkv|webm|avi|mov)(\?.*)?$", s)))


def validate_url_or_path(s: str) -> Optional[str]:
    s = (s or "").strip()
    if not s:
        return None
    # Local file?
    p = Path(s)
    if p.exists():
        return str(p)
    # http/https
    if s.lower().startswith(("http://", "https://")):
        return s
    # tapeciarnia scheme
    if s.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", s, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def current_system_locale() -> str:
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            return loc.split("_")[0]
    except Exception:
        pass
    return "en"


# -------------------------
# Desktop wallpaper helpers
# -------------------------
def get_current_desktop_wallpaper() -> Optional[str]:
    if sys.platform.startswith("win"):
        try:
            import ctypes
            buf = ctypes.create_unicode_buffer(260)
            SPI_GETDESKWALLPAPER = 0x0073
            ctypes.windll.user32.SystemParametersInfoW(SPI_GETDESKWALLPAPER, 260, buf, 0)
            return buf.value or None
        except Exception:
            return None
    elif sys.platform.startswith("linux"):
        try:
            res = subprocess.run(["gsettings", "get", "org.gnome.desktop.background", "picture-uri"],
                                  capture_output=True, text=True)
            if res.returncode == 0:
                val = res.stdout.strip().strip("'\"")
                if val.startswith("file://"):
                    return val[7:]
                return val
        except Exception:
            pass
        return None
    else:
        return None


def set_static_desktop_wallpaper(path: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            import ctypes
            SPI_SETDESKWALLPAPER = 20
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, str(path), 3)
            return True
        elif sys.platform.startswith("linux"):
            uri = f"file://{str(path)}"
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", uri], check=False)
            return True
    except Exception:
        return False
    return False


# -------------------------
# Wallpaper Controller
# -------------------------
class WallpaperController:
    def __init__(self):
        self.player_procs = []
        self.current_is_video = False

    def stop(self):
        if sys.platform.startswith("linux"):
            subprocess.call("pkill -f xwinwrap", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("pkill -f mpv", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            subprocess.call("taskkill /F /IM mpv.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM ffplay.exe", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for p in list(self.player_procs):
            try:
                p.terminate()
            except Exception:
                pass
        self.player_procs = []
        self.current_is_video = False

    def start_video(self, video_path_or_url: str):
        """Starts a video. If it's a URL and mpv exists, stream; otherwise play local file."""
        self.stop()
        self.current_is_video = True
        # If remote URL and mpv available -> stream (prefer)
        if str(video_path_or_url).lower().startswith("http"):
            mpv = which("mpv")
            if mpv:
                # try streaming
                try:
                    p = subprocess.Popen([mpv, "--loop", "--no-audio", "--no-osd-bar", "--fullscreen", "--no-border", video_path_or_url],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception:
                    pass
        # Otherwise treat as local file
        if sys.platform.startswith("linux"):
            # prefer xwinwrap + mpv if both available
            xw = which("xwinwrap")
            mpv = which("mpv")
            if xw and mpv:
                try:
                    cmd = f"{xw} -ov -fs -- {mpv} --loop --no-audio --no-osd-bar --wid=WID '{video_path_or_url}'"
                    p = subprocess.Popen(cmd, shell=True, executable="/bin/bash", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception:
                    pass
            if mpv:
                try:
                    p = subprocess.Popen([mpv, "--loop", "--no-audio", "--no-osd-bar", "--fullscreen", "--no-border", str(video_path_or_url)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.player_procs.append(p)
                    return
                except Exception:
                    pass
            raise RuntimeError("No mpv (or suitable player) found on Linux.")
        else:
            # Windows fallback: mpv or ffplay
            mpv = which("mpv")
            if mpv:
                p = subprocess.Popen([mpv, "--loop", "--no-audio", "--fullscreen", "--no-border", str(video_path_or_url)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                return
            ffplay = which("ffplay")
            if ffplay:
                cmd = f'start "" /min "{ffplay}" -autoexit -loop 0 -an -fs "{video_path_or_url}"'
                subprocess.Popen(cmd, shell=True)
                return
            raise RuntimeError("No player found (mpv/ffplay)")

    def start_image(self, image_path: str, fade_widget=None):
        """Set static wallpaper; optionally use fade_widget for visual transition."""
        self.stop()
        self.current_is_video = False
        try:
            set_static_desktop_wallpaper(image_path)
        except Exception:
            pass
        # UI fade handled by caller if provided
        return

    # convenience alias used in UI code
    def set_wallpaper(self, path_or_url: str, fade_widget=None):
        p = Path(str(path_or_url))
        if p.exists() and p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            self.start_image(str(p), fade_widget=fade_widget)
        else:
            # If remote image URL, download then set (caller often handles direct images)
            self.start_image(str(path_or_url), fade_widget=fade_widget)


# -------------------------
# Autopause Controller
# -------------------------
class AutoPauseController:
    def __init__(self):
        self.proc = None

    def autopause_path(self) -> Optional[Path]:
        candidates = [
            BASE_DIR / "bin" / "tools" / "autopause.exe",
            BASE_DIR / "bin" / "tools" / "autopause",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def start(self) -> bool:
        path = self.autopause_path()
        if path:
            try:
                self.proc = subprocess.Popen([str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                self.proc = None
        return False

    def stop(self):
        if self.proc:
            try:
                self.proc.terminate()
            except Exception:
                pass
            self.proc = None


# -------------------------
# Downloader thread (yt_dlp) - IMPROVED
# -------------------------
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
            from pathlib import Path
        except Exception as e:
            # yt_dlp missing -> notify UI
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
                        # total bytes may be missing; use estimate if available
                        total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                        downloaded = d.get("downloaded_bytes", 0)
                        percent = 0.0
                        if total:
                            try:
                                percent = float(downloaded) / float(total) * 100.0
                            except Exception:
                                percent = 0.0
                        else:
                            # If total unknown, use percentage from 'elapsed' vs 'duration' if provided (rare)
                            percent = d.get("progress", 0.0) or 0.0

                        # Speed
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

                        # ETA
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
                        # Emit safe values
                        try:
                            self.progress.emit(percent, status_msg)
                        except Exception:
                            pass

                    elif status == "finished":
                        # Show 100% briefly then finish
                        try:
                            self.progress.emit(100.0, "Processing...")
                        except Exception:
                            pass
                        time.sleep(0.3)
                except Exception:
                    # never let the hook raise — just ignore errors silently
                    pass

            # Use temporary downloads folder (will be organized later)
            outtmpl = str(COLLECTION_DIR / "%(title)s.%(ext)s")

            print(f"DEBUG: Downloading to: {outtmpl}")

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

                # Try to determine actual filename
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
                    # possible.append(Path(filename).with_suffix(".temp"))
                # Also check COLLECTION_DIR newest files as fallback
                existing = next((p for p in possible if p.exists()), None)
                if not existing:
                    # fallback: newest regular file in collection dir
                    try:
                        candidates = sorted(
                            [p for p in Path(COLLECTION_DIR).iterdir() if p.is_file()],
                            key=lambda x: x.stat().st_mtime,
                            reverse=True
                        )
                        existing = candidates[0] if candidates else None
                    except Exception:
                        existing = None

                if not existing:
                    # Could not find the file — error out
                    raise FileNotFoundError("Download finished but file not found in collection folder.")

                # Write temp marker (best-effort)
                try:
                    TMP_DOWNLOAD_FILE.write_text(str(existing.resolve()), encoding="utf-8")
                except Exception:
                    pass

                # Emit done with the real path
                try:
                    self.done.emit(str(existing.resolve()))
                except Exception:
                    # best-effort fallback
                    try:
                        self.done.emit(str(existing))
                    except Exception:
                        self.done.emit("")

        except Exception as e:
            # Bubble up error message to UI
            try:
                self.error.emit(str(e))
            except Exception:
                pass
            try:
                self.done.emit("")
            except Exception:
                pass


# -------------------------
# UI Fade overlay (image cross-fade)
# -------------------------
class FadeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._pixmap_old = None
        self._pixmap_new = None
        self._opacity = 0.0
        self._anim = None
        if parent:
            self.resize(parent.size())
        else:
            self.resize(800, 600)

    def set_pixmaps(self, old, new):
        self._pixmap_old = old
        self._pixmap_new = new
        self._opacity = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._pixmap_old:
            painter.setOpacity(1.0)
            painter.drawPixmap(self.rect(), self._pixmap_old)
        if self._pixmap_new:
            painter.setOpacity(self._opacity)
            painter.drawPixmap(self.rect(), self._pixmap_new)

    def animate_to(self, duration=600):
        anim = QPropertyAnimation(self, b"overlayOpacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._anim = anim

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, v):
        self._opacity = float(v)
        self.update()

    overlayOpacity = Property(float, getOpacity, setOpacity)


# -------------------------
# Download progress dialog
# -------------------------
# -------------------------
# Download progress dialog - FIXED VERSION
# -------------------------
class DownloadProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloading Video")
        self.setModal(True)
        self.setFixedSize(400, 120)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel("Preparing download...", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress = QProgressBar(self)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        
        # Add percentage label
        self.percentage_label = QLabel("0%", self)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        # Add details label for speed and ETA
        self.details_label = QLabel("Starting download...", self)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("font-size: 11px; color: #666;")
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.percentage_label)
        layout.addWidget(self.details_label)

    def update_progress(self, percent: float, status_msg: str = ""):
        percent_int = int(percent)
        self.progress.setValue(percent_int)
        self.percentage_label.setText(f"{percent_int}%")
        
        if status_msg:
            # Extract the main status and details
            if "Downloading..." in status_msg:
                details = status_msg.replace("Downloading... ", "")
                self.details_label.setText(details)
            else:
                self.details_label.setText(status_msg)
        
        # Ensure UI updates in real-time
        QApplication.processEvents()


# -------------------------
# Main app window
# -------------------------
class MP4WallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # controllers
        self.controller = WallpaperController()
        self.autopause = AutoPauseController()

        # UI / overlay
        self.fade_overlay = FadeOverlay(self)
        self.fade_overlay.hide()

        # scheduler
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self._scheduler_tick)
        self.scheduler_source = None
        self.scheduler_interval_minutes = 30
        
        # Range tracking
        self.current_range = "all"  # default to all

        # previous wallpaper
        self.previous_wallpaper = get_current_desktop_wallpaper()

        # autobind ui controls
        self._autobind_ui()

        # enable drag/drop on window
        self.setAcceptDrops(True)

        # tray
        self._setup_tray()

        # translations
        self._load_translations()

        # last saved
        self._load_last_video()
        
        # Load range preference
        self._load_range_preference()

        # CLI / URI
        self._handle_cli_args()
        
        # NEW: Set random wallpaper on startup if scheduler is disabled
        self._set_initial_wallpaper()

    def _set_initial_wallpaper(self):
        """Set random wallpaper on startup if scheduler is not enabled"""
        # Check if scheduler is disabled in config
        try:
            if CONFIG_PATH.exists():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                scheduler_enabled = cfg.get("scheduler_enabled", False)
                
                # If scheduler is not enabled and we have media files, set random wallpaper
                if not scheduler_enabled:
                    # Wait a bit for UI to load, then set random wallpaper
                    QTimer.singleShot(1000, self._set_random_startup_wallpaper)
        except Exception:
            pass

    def _set_random_startup_wallpaper(self):
        """Set a random wallpaper on startup"""
        # Check if we have any media files
        all_files = self._get_media_files(media_type="all")
        
        if all_files:
            # Randomly choose between image and video based on available files
            images = [f for f in all_files if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.bmp', '.gif')]
            videos = [f for f in all_files if f.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov')]
            
            if images and videos:
                # If we have both, randomly choose between image or video
                if random.choice([True, False]):
                    selected = random.choice(images)
                    self._apply_image_with_fade(str(selected))
                else:
                    selected = random.choice(videos)
                    self.autopause.start()
                    self.controller.start_video(str(selected))
            elif images:
                selected = random.choice(images)
                self._apply_image_with_fade(str(selected))
            elif videos:
                selected = random.choice(videos)
                self.autopause.start()
                self.controller.start_video(str(selected))
            
            if selected:
                self._save_last_video(str(selected))
                self._set_status(f"Started with: {selected.name}")
                
                # Update URL input
                if self.url_input:
                    self.url_input.setText(str(selected))

    def _load_range_preference(self):
        """Load range preference from config"""
        try:
            if CONFIG_PATH.exists():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                range_pref = cfg.get("range_preference", "all")
                self.current_range = range_pref
                self._update_range_buttons_active(range_pref)
        except Exception:
            self.current_range = "all"

    def _autobind_ui(self):
        attrs = getattr(self.ui, "__dict__", {})
        self.url_input = attrs.get("urlInput")
        self.status_label = attrs.get("statusLabel")

        # Buttons
        apply_names = ("applyButton", "loadUrlButton", "pushButton_apply", "pushButton")
        self.apply_btn = None
        for name in apply_names:
            if name in attrs:
                self.apply_btn = attrs[name]
                self.apply_btn.clicked.connect(self.on_apply_clicked)
                break
        self.reset_btn = attrs.get("resetButton")
        if self.reset_btn:
            self.reset_btn.clicked.connect(self.on_reset_clicked)
        self.browse_btn = attrs.get("browseButton")
        if self.browse_btn:
            self.browse_btn.clicked.connect(self.on_browse_clicked)

        # interval spinbox
        self.interval_spinbox = attrs.get("interval_spinBox")
        if self.interval_spinbox:
            self.interval_spinbox.valueChanged.connect(self._on_interval_changed)

        # explicit loadUrlButton (UI has that)
        if hasattr(self.ui, "loadUrlButton"):
            try:
                self.ui.loadUrlButton.clicked.connect(self.on_apply_clicked)
            except Exception:
                pass

        # NEW: Connect all the additional buttons
        self._connect_additional_buttons()

    def _connect_additional_buttons(self):
        """Connect all the additional functionality buttons"""
        # Shuffle buttons
        if hasattr(self.ui, "randomAnimButton"):
            self.ui.randomAnimButton.clicked.connect(self.on_shuffle_animated)
        
        if hasattr(self.ui, "randomButton"):
            self.ui.randomButton.clicked.connect(self.on_shuffle_wallpaper)
        
        # Wallpaper source buttons
        if hasattr(self.ui, "super_wallpaper_btn"):
            self.ui.super_wallpaper_btn.clicked.connect(self.on_super_wallpaper)
        
        if hasattr(self.ui, "fvrt_wallpapers_btn"):
            self.ui.fvrt_wallpapers_btn.clicked.connect(self.on_favorite_wallpapers)
        
        if hasattr(self.ui, "added_wallpaper_btn"):
            self.ui.added_wallpaper_btn.clicked.connect(self.on_added_wallpapers)
        
        # Range buttons
        if hasattr(self.ui, "range_all_bnt"):
            self.ui.range_all_bnt.clicked.connect(lambda: self.on_range_changed("all"))
        
        if hasattr(self.ui, "range_wallpaper_bnt"):
            self.ui.range_wallpaper_bnt.clicked.connect(lambda: self.on_range_changed("wallpaper"))
        
        if hasattr(self.ui, "range_mp4_bnt"):
            self.ui.range_mp4_bnt.clicked.connect(lambda: self.on_range_changed("mp4"))
        
        # Scheduler checkbox
        if hasattr(self.ui, "enabledCheck"):
            self.ui.enabledCheck.toggled.connect(self.on_scheduler_toggled)

    # Shuffle functionality
    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers (videos) based on current Range selection"""
        self._set_status("Shuffling animated wallpapers...")
        
        # Get video files based on current range selection
        video_files = self._get_media_files(media_type="mp4")
        
        if not video_files:
            QMessageBox.information(self, "No Videos", 
                                f"No animated wallpapers found in {self._get_range_display_name()} collection.")
            return
        
        # Randomly select a video
        selected_video = random.choice(video_files)
        
        try:
            self.autopause.start()
            self.controller.start_video(str(selected_video))
            self._save_last_video(str(selected_video))
            self._set_status(f"Playing: {selected_video.name}")
            
            # Update URL input to show current file
            if self.url_input:
                self.url_input.setText(str(selected_video))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play video: {e}")

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers (images) based on current Range selection"""
        self._set_status("Shuffling wallpapers...")
        
        # Get image files based on current range selection
        image_files = self._get_media_files(media_type="wallpaper")
        
        if not image_files:
            QMessageBox.information(self, "No Images", 
                                f"No wallpapers found in {self._get_range_display_name()} collection.")
            return
        
        # Randomly select an image
        selected_image = random.choice(image_files)
        
        try:
            self._apply_image_with_fade(str(selected_image))
            self._save_last_video(str(selected_image))
            self._set_status(f"Applied: {selected_image.name}")
            
            # Update URL input to show current file
            if self.url_input:
                self.url_input.setText(str(selected_image))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply image: {e}")

    def _get_media_files(self, media_type="all"):
        """Get media files from organized collection based on current Range selection"""
        files = []
        
        # Define which folders to search based on Range and media type
        if media_type == "mp4":  # Videos only
            search_folders = [VIDEOS_DIR, FAVS_DIR]
            extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        elif media_type == "wallpaper":  # Images only  
            search_folders = [IMAGES_DIR, FAVS_DIR]
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        else:  # All media types
            search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mkv', '.webm', '.avi', '.mov')
        
        # Collect files from specified folders
        for folder in search_folders:
            if folder.exists():
                folder_files = [
                    f for f in folder.iterdir() 
                    if f.is_file() and f.suffix.lower() in extensions
                ]
                files.extend(folder_files)
        
        return files
    
    def _get_range_display_name(self):
        """Get display name for current range selection"""
        range_names = {
            "all": "All",
            "wallpaper": "Wallpaper", 
            "mp4": "MP4"
        }
        return range_names.get(self.current_range, "All")

    # Wallpaper source functionality
    def on_super_wallpaper(self):
        """Handle Super Wallpaper source selection"""
        self._set_status("Super Wallpaper source selected")
        # Here you can implement premium/curated wallpaper sources
        # For now, we'll use a placeholder
        QMessageBox.information(self, "Super Wallpaper", 
                            "Super Wallpaper feature - Premium curated wallpapers coming soon!")
        
        # You can implement API calls to premium wallpaper services here
        # Example: self._load_from_premium_source()

    def on_favorite_wallpapers(self):
        """Use favorite wallpapers as source"""
        self._set_status("Favorite wallpapers source selected")
        
        if not FAVS_DIR.exists() or not any(FAVS_DIR.iterdir()):
            QMessageBox.information(self, "No Favorites", 
                                "No favorite wallpapers found. Add some wallpapers to favorites first.")
            return
        
        # Set scheduler to use favorites folder
        self.scheduler_source = str(FAVS_DIR)
        self._set_status("Scheduler set to use favorite wallpapers")
        
        # Update UI to show active source
        self._update_source_buttons_active("favorites")

    def on_added_wallpapers(self):
        """Use the entire organized collection as source"""
        self._set_status("My Collection source selected")
        
        # Check if we have any files in the organized collection
        has_videos = VIDEOS_DIR.exists() and any(VIDEOS_DIR.iterdir())
        has_images = IMAGES_DIR.exists() and any(IMAGES_DIR.iterdir())
        has_favorites = FAVS_DIR.exists() and any(FAVS_DIR.iterdir())
        
        if not (has_videos or has_images or has_favorites):
            QMessageBox.information(self, "Empty Collection", 
                                "No wallpapers found in your collection. Download or add some wallpapers first.")
            return
        
        # Set scheduler to use the entire organized collection
        self.scheduler_source = str(COLLECTION_DIR)
        self._set_status("Scheduler set to use entire collection")
        
        # Update UI to show active source
        self._update_source_buttons_active("added")

    def _update_source_buttons_active(self, active_source):
        """Update button styles to show which source is active"""
        sources = {
            "super": self.ui.super_wallpaper_btn if hasattr(self.ui, "super_wallpaper_btn") else None,
            "favorites": self.ui.fvrt_wallpapers_btn if hasattr(self.ui, "fvrt_wallpapers_btn") else None,
            "added": self.ui.added_wallpaper_btn if hasattr(self.ui, "added_wallpaper_btn") else None
        }
        
        # Reset all to ghost style
        for btn in sources.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        # Set active one to primary style
        if active_source in sources and sources[active_source]:
            sources[active_source].setProperty("class", "primary")
            sources[active_source].style().unpolish(sources[active_source])
            sources[active_source].style().polish(sources[active_source])

    # Range functionality
    def on_range_changed(self, range_type):
        """Handle range selection (All, Wallpaper, MP4)"""
        self.current_range = range_type
        self._set_status(f"Range set to: {range_type}")
        
        # Update button styles
        self._update_range_buttons_active(range_type)
        
        # Store range preference in config
        self._save_range_preference(range_type)
        
        # If scheduler is active, restart it with new range
        if self.scheduler_timer.isActive():
            self._restart_scheduler_with_new_range()

    def _restart_scheduler_with_new_range(self):
        """Restart scheduler when range changes"""
        if self.scheduler_source:
            self.stop_scheduler()
            self.start_scheduler(self.scheduler_source, self.scheduler_interval_minutes)
            self._set_status(f"Scheduler updated with {self.current_range} range")

    def _update_range_buttons_active(self, active_range):
        """Update range button styles to show which is active"""
        range_buttons = {
            "all": self.ui.range_all_bnt if hasattr(self.ui, "range_all_bnt") else None,
            "wallpaper": self.ui.range_wallpaper_bnt if hasattr(self.ui, "range_wallpaper_bnt") else None,
            "mp4": self.ui.range_mp4_bnt if hasattr(self.ui, "range_mp4_bnt") else None
        }
        
        # Reset all to ghost style
        for btn in range_buttons.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        # Set active one to primary style
        if active_range in range_buttons and range_buttons[active_range]:
            range_buttons[active_range].setProperty("class", "primary")
            range_buttons[active_range].style().unpolish(range_buttons[active_range])
            range_buttons[active_range].style().polish(range_buttons[active_range])

    def _save_range_preference(self, range_type):
        """Save range preference to config"""
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                try:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            cfg["range_preference"] = range_type
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as e:
            print("[CONFIG] range save failed:", e)

    # Scheduler functionality
    def on_scheduler_toggled(self, enabled):
        """Handle scheduler enable/disable"""
        if enabled:
            if not self.scheduler_source:
                # Default to main collection folder
                self.scheduler_source = str(COLLECTION_DIR)
                self._set_status("Scheduler enabled - using entire collection")
            else:
                self._set_status(f"Scheduler enabled - using {Path(self.scheduler_source).name}")
            
            # Start scheduler with current interval
            interval = self.scheduler_interval_minutes
            if hasattr(self.ui, "interval_spinBox"):
                interval = self.ui.interval_spinBox.value()
            
            self.start_scheduler(self.scheduler_source, interval)
        else:
            self.stop_scheduler()
        
        # Save scheduler state
        self._save_scheduler_state(enabled)

    def _save_scheduler_state(self, enabled):
        """Save scheduler enabled/disabled state"""
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                try:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            cfg["scheduler_enabled"] = enabled
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as e:
            print("[CONFIG] scheduler state save failed:", e)

    # Enhanced scheduler with range filtering
    def _scheduler_tick(self):
        """Scheduler tick that respects current Range selection"""
        if not self.scheduler_source:
            return
            
        src = self.scheduler_source
        if Path(src).exists() and Path(src).is_dir():
            # Get files based on current range selection
            files = self._get_media_files(media_type="all")  # Get all media types, range filtering happens in the method
            
            if not files:
                self._set_status(f"Scheduler: no {self.current_range} media found")
                return
                
            chosen = str(random.choice(files))
            self._apply_input_string(chosen)
            self._set_status(f"Auto-changed: {Path(chosen).name}")
        else:
            # treat as URL playlist -> download first item
            self.downloader = DownloaderThread(src)
            self.downloader.done.connect(self._on_download_done)
            self.downloader.start()
    
    def add_to_favorites(self, file_path: str):
        """Add a wallpaper to favorites"""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                self._set_status("File not found for favorites")
                return False
                
            # Copy to favorites folder
            fav_path = FAVS_DIR / source_path.name
            if not fav_path.exists():
                shutil.copy2(source_path, fav_path)
                self._set_status(f"Added to favorites: {source_path.name}")
                return True
            else:
                self._set_status("Already in favorites")
                return True
                
        except Exception as e:
            self._set_status(f"Failed to add to favorites: {e}")
        return False

    def remove_from_favorites(self, file_path: str):
        """Remove a wallpaper from favorites"""
        try:
            fav_path = FAVS_DIR / Path(file_path).name
            if fav_path.exists():
                fav_path.unlink()
                self._set_status(f"Removed from favorites: {fav_path.name}")
                return True
            else:
                self._set_status("File not in favorites")
                return False
                
        except Exception as e:
            self._set_status(f"Failed to remove from favorites: {e}")
            return False

    def _set_status(self, s: str):
        if self.status_label:
            try:
                self.status_label.setText(s)
            except Exception:
                print("[status]", s)
        else:
            print("[status]", s)

    # Drag/drop events
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if not urls:
            return
        p = urls[0].toLocalFile()
        if not p:
            return
        p = str(Path(p))
        self._set_status(f"Dropped: {Path(p).name}")
        self._apply_input_string(p)

    # CLI / URI handling
    def _handle_cli_args(self):
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            parsed = validate_url_or_path(arg) or (re.match(r"tapeciarnia:\[?(.*)\]?$", arg, re.IGNORECASE) and re.match(r"tapeciarnia:\[?(.*)\]?$", arg, re.IGNORECASE).group(1))
            if parsed:
                self._set_status("Applying from URI...")
                self._apply_input_string(parsed)

    # Browse local
    def on_browse_clicked(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select video or image", str(Path.home()),
                                              "Media (*.mp4 *.mkv *.webm *.avi *.mov *.jpg *.jpeg *.png)")
        if path:
            if self.url_input:
                try:
                    self.url_input.setText(path)
                except Exception:
                    pass
            self._apply_input_string(path)

    def on_apply_clicked(self):
        if not self.url_input:
            QMessageBox.warning(self, "Error", "No input field available in UI")
            return
        s = self.url_input.text().strip()
        if not s:
            QMessageBox.warning(self, "Error", "No URL/path provided")
            return
        self._apply_input_string(s)
    
    def _on_download_error(self, error_msg: str):
        """Handle download errors and close progress dialog"""
        try:
            if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
                self.progress_dialog.close()
        except Exception:
            pass
        QMessageBox.critical(self, "Download Error", error_msg)
        self._set_status(f"Download failed: {error_msg}")

    def _apply_input_string(self, text: str):
        print(f"DEBUG: COLLECTION_DIR: {COLLECTION_DIR}")
        print(f"DEBUG: VIDEOS_DIR: {VIDEOS_DIR}")
        print(f"DEBUG: IMAGES_DIR: {IMAGES_DIR}")
        print(f"DEBUG: Do folders exist?")
        print(f"DEBUG: - COLLECTION_DIR: {COLLECTION_DIR.exists()}")
        print(f"DEBUG: - VIDEOS_DIR: {VIDEOS_DIR.exists()}")
        print(f"DEBUG: - IMAGES_DIR: {IMAGES_DIR.exists()}")
    
        text = (text or "").strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter a valid URL or file path.")
            return

        validated = validate_url_or_path(text)
        print(f"DEBUG: Validated input: {validated}") 
        if not validated:
            QMessageBox.warning(self, "Error", f"Input not recognized: {text}")
            return

        # Ensure collection folders exist before processing
        self._ensure_collection_folders()

        # Local path?
        p = Path(validated)
        if p.exists():
            if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
                # Copy to videos collection
                dest = VIDEOS_DIR / p.name
                try:
                    if not dest.exists():
                        shutil.copy2(p, dest)
                        self._set_status(f"Video added to collection: {p.name}")
                    else:
                        self._set_status(f"Video already in collection: {p.name}")
                except Exception as e:
                    print(f"DEBUG: Failed to copy video to collection: {e}")
                    dest = p  # Use original if copy fails
                    
                try:
                    self.autopause.start()
                    self.controller.start_video(str(dest))
                    self._save_last_video(str(dest))
                    self._set_status(f"Playing: {p.name}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to play video: {e}")
                return
                
            elif p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
                # Copy to images collection  
                dest = IMAGES_DIR / p.name
                try:
                    if not dest.exists():
                        shutil.copy2(p, dest)
                        self._set_status(f"Image added to collection: {p.name}")
                    else:
                        self._set_status(f"Image already in collection: {p.name}")
                except Exception as e:
                    print(f"DEBUG: Failed to copy image to collection: {e}")
                    dest = p  # Use original if copy fails
                    
                try:
                    self._apply_image_with_fade(str(dest))
                    self._save_last_video(str(dest))
                    self._set_status(f"Applied: {p.name}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to apply image: {e}")
                return
            else:
                QMessageBox.warning(self, "Unsupported", "Unsupported local file type.")
                return

        # Remote URL
        if validated.lower().startswith("http"):
            # Direct image URL?
            if is_image_url_or_path(validated):
                self._set_status("Downloading image...")
                try:
                    import requests
                    r = requests.get(validated, stream=True, timeout=30)
                    r.raise_for_status()
                    
                    ext = Path(validated).suffix 
                    if not ext or ext.lower() not in ('.jpg', '.jpeg', '.png', '.bmp', '.gif'):
                        ext = '.jpg'  # Default extension
                        
                    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(validated).stem)[:60]
                    dest = IMAGES_DIR / f"{safe}{ext}"
                    
                    # Ensure Images folder exists
                    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                    
                    with open(dest, "wb") as fh:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                fh.write(chunk)
                    
                    self._apply_image_with_fade(str(dest))
                    self._save_last_video(str(dest))
                    self._set_status(f"Image saved to collection: {dest.name}")
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to download image: {e}")
                return

            # For video URLs: ALWAYS DOWNLOAD (skip streaming)
            self._set_status("Downloading video...")
            print(f"DEBUG: Starting video download: {validated}")
            
            try:
                # remove any stale temp marker
                if TMP_DOWNLOAD_FILE.exists():
                    try:
                        TMP_DOWNLOAD_FILE.unlink()
                    except Exception:
                        pass

                # Ensure Videos folder exists
                VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

                # create and show progress dialog
                self.progress_dialog = DownloadProgressDialog(self)
                self.progress_dialog.setWindowTitle("Downloading Video")

                # create downloader thread
                self.downloader = DownloaderThread(validated)

                # wire signals
                self.downloader.progress.connect(
                    lambda percent, status: (
                        self.progress_dialog.update_progress(percent, status),
                        self._set_status(status)  # Also update main status
                    )
                )
                self.downloader.error.connect(self._on_download_error)
                
                def _done_handler(path_str):
                    # ensure dialog closes first
                    try:
                        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
                            self.progress_dialog.close()
                    except Exception:
                        pass
                    # forward to existing handler
                    self._on_download_done(path_str)

                self.downloader.done.connect(_done_handler)

                # run downloader
                self.downloader.start()

                # show progress dialog
                self.progress_dialog.show()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Download setup failed: {e}")
            return

        QMessageBox.warning(self, "Invalid Input", "Unsupported input type.")

    def _ensure_collection_folders(self):
        """Ensure all collection folders exist with proper permissions"""
        try:
            folders = [COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
            for folder in folders:
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    print(f"DEBUG: Folder ready: {folder}")
                except Exception as e:
                    print(f"DEBUG: Failed to create {folder}: {e}")
                    # Try alternative location as fallback
                    if folder == COLLECTION_DIR:
                        alt_dir = Path.home() / "Tapeciarnia"
                        alt_dir.mkdir(parents=True, exist_ok=True)
                        print(f"DEBUG: Using alternative location: {alt_dir}")
        except Exception as e:
            print(f"DEBUG: Critical folder error: {e}")

    def _on_download_done(self, path: str):
        """Handle completion of downloads — save to organized collection"""
        if not path:
            self._set_status("Download failed or produced no usable file.")
            return

        p = Path(path)
        if not p.exists():
            self._set_status("Downloaded file missing.")
            return

        # ✅ Determine the correct destination folder based on file type
        if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            dest_folder = VIDEOS_DIR
            file_type = "video"
        elif p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            dest_folder = IMAGES_DIR
            file_type = "image"
        else:
            dest_folder = COLLECTION_DIR  # Fallback
            file_type = "file"

        # Save to appropriate collection folder
        collection_dest = dest_folder / p.name
        
        try:
            if not collection_dest.exists():
                shutil.copy2(p, collection_dest)
                self._set_status(f"{file_type.capitalize()} saved to collection: {collection_dest.name}")
            else:
                # File already exists in collection
                self._set_status(f"{file_type.capitalize()} already in collection: {collection_dest.name}")
        except Exception as e:
            print(f"[WARN] Failed to copy to collection: {e}")
            collection_dest = p

        # Apply the wallpaper
        self._apply_wallpaper_from_path(collection_dest)

    def _apply_wallpaper_from_path(self, file_path: Path):
        """Apply wallpaper from a file path"""
        # Video handling
        if file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            try:
                self.autopause.start()
                self.controller.start_video(str(file_path))
                self._save_last_video(str(file_path))
                self._set_status(f"Playing video: {file_path.name}")
                self._add_to_recent_wallpapers(str(file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to play video: {e}")
        
        # Image handling  
        elif file_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            try:
                self._apply_image_with_fade(str(file_path))
                self._save_last_video(str(file_path))
                self._set_status(f"Wallpaper set: {file_path.name}")
                self._add_to_recent_wallpapers(str(file_path))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to set image: {e}")
        
        else:
            QMessageBox.warning(self, "Unsupported", f"File type not supported: {file_path.suffix}")

    def _add_to_recent_wallpapers(self, file_path: str):
        """Add to recently used wallpapers"""
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                try:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            
            recent = cfg.get("recent_wallpapers", [])
            
            # Add to beginning, remove duplicates, limit to 20
            if file_path in recent:
                recent.remove(file_path)
            recent.insert(0, file_path)
            recent = recent[:20]  # Keep only last 20
            
            cfg["recent_wallpapers"] = recent
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as e:
            print("[CONFIG] recent wallpapers save failed:", e)

    def _apply_image_with_fade(self, image_path: str):
        try:
            old_pix = None
            try:
                old_pix = self.grab()
            except Exception:
                old_pix = None
            new_pix = QPixmap(image_path)
            new_pix = new_pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.fade_overlay.set_pixmaps(old_pix, new_pix)
            self.fade_overlay.show()
            self.fade_overlay.raise_()
            self.fade_overlay.animate_to(duration=650)
            set_static_desktop_wallpaper(image_path)
            QTimer.singleShot(700, self.fade_overlay.hide)
            self._set_status(f"Image applied: {Path(image_path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fade apply failed: {e}")

    # Reset
    def on_reset_clicked(self):
        self._perform_reset()

    def _perform_reset(self):
        try:
            self.controller.stop()
        except Exception:
            pass
        try:
            self.autopause.stop()
        except Exception:
            pass
        if self.previous_wallpaper:
            ok = set_static_desktop_wallpaper(self.previous_wallpaper)
            if ok:
                self._set_status("Restored previous wallpaper")
                return
        self._set_status("Reset complete (no previous wallpaper)")

    # Scheduler
    def start_scheduler(self, source: str, interval_minutes: int = 30):
        self.scheduler_source = source
        self.scheduler_interval_minutes = max(1, int(interval_minutes))
        self.scheduler_timer.start(self.scheduler_interval_minutes * 60 * 1000)
        self._set_status(f"Scheduler started: every {self.scheduler_interval_minutes} min")

    def stop_scheduler(self):
        self.scheduler_timer.stop()
        self.scheduler_source = None
        self._set_status("Scheduler stopped")

    def _on_interval_changed(self, val):
        self.scheduler_interval_minutes = val
        if self.scheduler_timer.isActive():
            self.scheduler_timer.start(self.scheduler_interval_minutes * 60 * 1000)
            self._set_status(f"Scheduler interval: {val} min")

    # Persistence
    def _save_last_video(self, path: str):
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                try:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            cfg["last_video"] = path
            cfg["scheduler_source"] = self.scheduler_source
            cfg["scheduler_interval"] = self.scheduler_interval_minutes
            CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        except Exception as e:
            print("[CONFIG] save failed:", e)

    def _load_last_video(self):
        try:
            if CONFIG_PATH.exists():
                cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                last = cfg.get("last_video")
                sc = cfg.get("scheduler_source")
                si = cfg.get("scheduler_interval")
                if last and self.url_input:
                    try:
                        self.url_input.setText(last)
                    except Exception:
                        pass
                if sc:
                    self.scheduler_source = sc
                if si:
                    self.scheduler_interval_minutes = int(si)
                    if self.interval_spinbox:
                        try:
                            self.interval_spinbox.setValue(int(si))
                        except Exception:
                            pass
        except Exception:
            pass

    # Tray
    def _setup_tray(self):
        QApplication.setQuitOnLastWindowClosed(False)
        icon = QIcon()
        cand = BASE_DIR / "ui" / "icons" / "logo_biale.svg"
        if cand.exists():
            icon = QIcon(str(cand))
        self.tray = QSystemTrayIcon(icon, parent=self)
        menu = QMenu()
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        menu.addAction(show_action)
        menu.addAction(hide_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def _exit_app(self):
        try:
            self.controller.stop()
        except Exception:
            pass
        try:
            self.autopause.stop()
        except Exception:
            pass
        QApplication.quit()

    # Translations
    def _load_translations(self):
        try:
            cfg = {}
            if CONFIG_PATH.exists():
                try:
                    cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
                except Exception:
                    cfg = {}
            preferred = cfg.get("language") or current_system_locale()
            f = TRANSLATIONS_DIR / f"{preferred}.json"
            if not f.exists():
                f = TRANSLATIONS_DIR / "en.json"
            if f.exists():
                data = json.loads(f.read_text(encoding="utf-8"))
                self._apply_translation(data)
        except Exception:
            pass

    def _apply_translation(self, mapping: dict):
        for widget_name, text in mapping.items():
            if hasattr(self.ui, widget_name):
                w = getattr(self.ui, widget_name)
                try:
                    if hasattr(w, "setText"):
                        w.setText(text)
                except Exception:
                    pass


# -------------------------
# CLI helper
# -------------------------
def validate_cli_arg(arg: str) -> Optional[str]:
    parsed = validate_url_or_path(arg)
    if parsed:
        return parsed
    if arg.lower().startswith("tapeciarnia:"):
        m = re.match(r"tapeciarnia:\[?(.*)\]?$", arg, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


# -------------------------
# Entry point
# -------------------------
def main():
    app = QApplication(sys.argv)
    window = MP4WallApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
