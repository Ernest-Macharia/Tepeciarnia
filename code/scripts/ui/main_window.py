import os
import sys
import random
import shutil
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QSystemTrayIcon, QMenu
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtCore import QTimer, Qt, QEvent, QCoreApplication

current_dir = os.path.dirname(__file__)
ui_path = os.path.join(current_dir, 'mainUI.py')
sys.path.append(os.path.dirname(current_dir))

try:
    from ui.mainUI import Ui_MainWindow
except ImportError as e:
    logging.error(f"UI import error: {e}")
    # Try alternative import path
    try:
        sys.path.append(current_dir)
        from mainUI import Ui_MainWindow
    except ImportError:
        raise ImportError("Cannot import Ui_MainWindow. Make sure mainUI.py exists in the ui folder.")

# Import core modules
from core.wallpaper_controller import WallpaperController
from core.autopause_controller import AutoPauseController
from core.download_manager import DownloaderThread
from core.scheduler import WallpaperScheduler

# Import utilities
from utils.path_utils import COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR
from utils.system_utils import get_current_desktop_wallpaper
from utils.validators import validate_url_or_path, is_image_url_or_path
from utils.file_utils import download_image, copy_to_collection, cleanup_temp_marker

# Import models
from models.config import Config

# Import UI components
from .widgets import FadeOverlay
from .dialogs import DownloadProgressDialog


class MP4WallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize controllers
        self.controller = WallpaperController()
        self.autopause = AutoPauseController()
        self.scheduler = WallpaperScheduler()
        self.config = Config()

        # UI components
        self.fade_overlay = FadeOverlay(self)
        self.fade_overlay.hide()

        # State
        self.current_range = "all"
        self.previous_wallpaper = get_current_desktop_wallpaper()
        self.is_minimized_to_tray = False

        # Setup
        self._setup_ui()
        self._setup_tray()
        self._load_settings()
        self._handle_cli_args()

    def changeEvent(self, event):
        """
        Handle window state changes - ONLY minimize to tray on minimize button
        """
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and not self.is_minimized_to_tray:
                # User clicked minimize button - hide to system tray
                event.ignore()  # Ignore the minimize event
                self.hide_to_tray()
        super().changeEvent(event)

    def closeEvent(self, event):
        """
        Handle window close event - X button should CLOSE the application
        """
        # Stop any running processes
        self._perform_reset()
        
        # Hide tray icon and quit application
        if hasattr(self, 'tray'):
            self.tray.hide()
        
        QCoreApplication.quit()
        event.accept()

    def hide_to_tray(self):
        """Hide window to system tray with proper notification"""
        self.hide()
        self.is_minimized_to_tray = True
        
        if hasattr(self, 'tray'):
            # Show notification that app is still running
            self.tray.showMessage(
                "MP4 Wall",
                "Application is still running in system tray\nClick the tray icon to show the window",
                QSystemTrayIcon.Information,
                3000
            )

    def show_from_tray(self):
        """Show window from system tray"""
        self.show()
        self.raise_()
        self.activateWindow()
        # Ensure window is not minimized when showing from tray
        if self.isMinimized():
            self.showNormal()
        self.is_minimized_to_tray = False

    def _setup_ui(self):
        """Setup UI connections and initial state"""
        self.setAcceptDrops(True)
        
        # Connect signals
        self.scheduler.set_change_callback(self._apply_input_string)
        
        # Bind UI controls
        self._bind_ui_controls()

    def _bind_ui_controls(self):
        """Bind UI controls to their handlers"""
        # Main controls
        if hasattr(self.ui, "loadUrlButton"):
            self.ui.loadUrlButton.clicked.connect(self.on_apply_clicked)
        
        if hasattr(self.ui, "urlInput"):
            self.ui.urlInput.returnPressed.connect(self.on_apply_clicked)

        # Start/Reset buttons (now in Range section)
        if hasattr(self.ui, "startButton"):
            self.ui.startButton.clicked.connect(self.on_start_clicked)
        
        if hasattr(self.ui, "resetButton"):
            self.ui.resetButton.clicked.connect(self.on_reset_clicked)

        # Browse button
        if hasattr(self.ui, "browseButton"):
            self.ui.browseButton.clicked.connect(self.on_browse_clicked)

        # Shuffle buttons
        if hasattr(self.ui, "randomAnimButton"):
            self.ui.randomAnimButton.clicked.connect(self.on_shuffle_animated)
        
        if hasattr(self.ui, "randomButton"):
            self.ui.randomButton.clicked.connect(self.on_shuffle_wallpaper)

        # Source buttons
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

        # Scheduler controls
        if hasattr(self.ui, "enabledCheck"):
            self.ui.enabledCheck.toggled.connect(self.on_scheduler_toggled)
        
        if hasattr(self.ui, "interval_spinBox"):
            self.ui.interval_spinBox.valueChanged.connect(self._on_interval_changed)

    # Main application methods
    def on_apply_clicked(self):
        """Handle apply/load button click"""
        if not hasattr(self.ui, "urlInput"):
            QMessageBox.warning(self, "Error", "No input field available in UI")
            return
        
        url = self.ui.urlInput.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "No URL/path provided")
            return
        
        self._apply_input_string(url)

    def on_start_clicked(self):
        """Start the current wallpaper"""
        if hasattr(self.ui, "urlInput"):
            current_url = self.ui.urlInput.text().strip()
            if current_url:
                self._set_status("Starting wallpaper...")
                self._apply_input_string(current_url)
            else:
                QMessageBox.warning(self, "No Wallpaper", "Please load a wallpaper first.")

    def on_reset_clicked(self):
        """Reset to default wallpaper"""
        self._perform_reset()

    def on_browse_clicked(self):
        """Browse for local files"""
        path, _ = QFileDialog.getOpenFileName(
            self, "Select video or image", str(Path.home()),
            "Media (*.mp4 *.mkv *.webm *.avi *.mov *.jpg *.jpeg *.png)"
        )
        if path:
            if hasattr(self.ui, "urlInput"):
                self.ui.urlInput.setText(path)
            self._apply_input_string(path)

    # Shuffle functionality
    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers"""
        self._set_status("Shuffling animated wallpapers...")
        video_files = self._get_media_files(media_type="mp4")
        
        if not video_files:
            QMessageBox.information(self, "No Videos", 
                                f"No animated wallpapers found in {self._get_range_display_name()} collection.")
            return
        
        selected = random.choice(video_files)
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers"""
        self._set_status("Shuffling wallpapers...")
        image_files = self._get_media_files(media_type="wallpaper")
        
        if not image_files:
            QMessageBox.information(self, "No Images", 
                                f"No wallpapers found in {self._get_range_display_name()} collection.")
            return
        
        selected = random.choice(image_files)
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    # Source selection
    def on_super_wallpaper(self):
        """Super Wallpaper source"""
        self._set_status("Super Wallpaper source selected")
        QMessageBox.information(self, "Super Wallpaper", 
                            "Super Wallpaper feature - Premium curated wallpapers coming soon!")

    def on_favorite_wallpapers(self):
        """Favorite wallpapers source"""
        self._set_status("Favorite wallpapers source selected")
        
        if not FAVS_DIR.exists() or not any(FAVS_DIR.iterdir()):
            QMessageBox.information(self, "No Favorites", 
                                "No favorite wallpapers found. Add some wallpapers to favorites first.")
            return
        
        self.scheduler.source = str(FAVS_DIR)
        self._set_status("Scheduler set to use favorite wallpapers")
        self._update_source_buttons_active("favorites")

    def on_added_wallpapers(self):
        """My Collection source"""
        self._set_status("My Collection source selected")
        
        has_videos = VIDEOS_DIR.exists() and any(VIDEOS_DIR.iterdir())
        has_images = IMAGES_DIR.exists() and any(IMAGES_DIR.iterdir())
        has_favorites = FAVS_DIR.exists() and any(FAVS_DIR.iterdir())
        
        if not (has_videos or has_images or has_favorites):
            QMessageBox.information(self, "Empty Collection", 
                                "No wallpapers found in your collection. Download or add some wallpapers first.")
            return
        
        self.scheduler.source = str(COLLECTION_DIR)
        self._set_status("Scheduler set to use entire collection")
        self._update_source_buttons_active("added")

    # Range selection
    def on_range_changed(self, range_type):
        """Handle range selection"""
        self.current_range = range_type
        self.scheduler.set_range(range_type)
        self._set_status(f"Range set to: {range_type}")
        self._update_range_buttons_active(range_type)
        self.config.set_range_preference(range_type)

    # Scheduler controls
    def on_scheduler_toggled(self, enabled):
        """Handle scheduler enable/disable"""
        if enabled:
            if not self.scheduler.source:
                self.scheduler.source = str(COLLECTION_DIR)
                self._set_status("Scheduler enabled - using entire collection")
            
            interval = self.scheduler.interval_minutes
            if hasattr(self.ui, "interval_spinBox"):
                interval = self.ui.interval_spinBox.value()
            
            self.scheduler.start(self.scheduler.source, interval)
        else:
            self.scheduler.stop()
            self._set_status("Scheduler stopped")
        
        self.config.set_scheduler_settings(
            self.scheduler.source, 
            self.scheduler.interval_minutes, 
            enabled
        )

    def _on_interval_changed(self, val):
        """Handle interval change"""
        self.scheduler.interval_minutes = val
        if self.scheduler.is_active():
            self.scheduler.stop()
            self.scheduler.start(self.scheduler.source, val)
        self._set_status(f"Scheduler interval: {val} min")

    # Core wallpaper application logic
    def _apply_input_string(self, text: str):
        """Main method to apply wallpaper from various inputs"""
        text = (text or "").strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter a valid URL or file path.")
            return

        validated = validate_url_or_path(text)
        if not validated:
            QMessageBox.warning(self, "Error", f"Input not recognized: {text}")
            return

        # Handle local files
        p = Path(validated)
        if p.exists():
            self._handle_local_file(p)
            return

        # Handle remote URLs
        if validated.lower().startswith("http"):
            if is_image_url_or_path(validated):
                self._handle_remote_image(validated)
            else:
                self._handle_remote_video(validated)
            return

        QMessageBox.warning(self, "Invalid Input", "Unsupported input type.")

    def _handle_local_file(self, file_path: Path):
        """Handle local file application"""
        if file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            dest = copy_to_collection(file_path, VIDEOS_DIR)
            self._apply_video(str(dest))
        elif file_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            dest = copy_to_collection(file_path, IMAGES_DIR)
            self._apply_image_with_fade(str(dest))
        else:
            QMessageBox.warning(self, "Unsupported", "Unsupported local file type.")

    def _handle_remote_image(self, url: str):
        """Handle remote image download and application"""
        self._set_status("Downloading image...")
        try:
            local_path = download_image(url)
            self._apply_image_with_fade(local_path)
            self.config.set_last_video(local_path)
            self._set_status(f"Image saved to collection: {Path(local_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to download image: {e}")

    def _handle_remote_video(self, url: str):
        """Handle remote video download"""
        self._set_status("Downloading video...")
        cleanup_temp_marker()

        try:
            self.progress_dialog = DownloadProgressDialog(self)
            self.downloader = DownloaderThread(url)

            self.downloader.progress.connect(
                lambda percent, status: (
                    self.progress_dialog.update_progress(percent, status),
                    self._set_status(status)
                )
            )
            self.downloader.error.connect(self._on_download_error)
            self.downloader.done.connect(self._on_download_done)

            self.downloader.start()
            self.progress_dialog.show()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Download setup failed: {e}")

    def _on_download_done(self, path: str):
        """Handle download completion"""
        if self.progress_dialog and self.progress_dialog.isVisible():
            self.progress_dialog.close()

        if not path:
            self._set_status("Download failed or produced no usable file.")
            return

        p = Path(path)
        if not p.exists():
            self._set_status("Downloaded file missing.")
            return

        # Determine destination folder
        if p.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            dest_folder = VIDEOS_DIR
        elif p.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            dest_folder = IMAGES_DIR
        else:
            dest_folder = COLLECTION_DIR

        # Copy to collection
        collection_dest = dest_folder / p.name
        if not collection_dest.exists():
            shutil.copy2(p, collection_dest)

        self._apply_wallpaper_from_path(collection_dest)

    def _apply_wallpaper_from_path(self, file_path: Path):
        """Apply wallpaper from file path"""
        if file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            self._apply_video(str(file_path))
        elif file_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            self._apply_image_with_fade(str(file_path))
        else:
            QMessageBox.warning(self, "Unsupported", f"File type not supported: {file_path.suffix}")

    def _apply_video(self, video_path: str):
        """Apply video wallpaper"""
        try:
            self.autopause.start()
            self.controller.start_video(video_path)
            self.config.set_last_video(video_path)
            self._set_status(f"Playing video: {Path(video_path).name}")
            self._update_url_input(video_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to play video: {e}")

    def _apply_image_with_fade(self, image_path: str):
        """Apply image wallpaper with fade effect"""
        try:
            old_pix = self.grab() if hasattr(self, 'grab') else None
            new_pix = QPixmap(image_path)
            new_pix = new_pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            self.fade_overlay.set_pixmaps(old_pix, new_pix)
            self.fade_overlay.show()
            self.fade_overlay.raise_()
            self.fade_overlay.animate_to(duration=650)
            
            self.controller.start_image(image_path)
            self.config.set_last_video(image_path)
            
            QTimer.singleShot(700, self.fade_overlay.hide)
            self._set_status(f"Image applied: {Path(image_path).name}")
            self._update_url_input(image_path)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fade apply failed: {e}")

    # Utility methods
    def _get_media_files(self, media_type="all"):
        """Get media files based on current range"""
        files = []
        
        if media_type == "mp4":
            search_folders = [VIDEOS_DIR, FAVS_DIR]
            extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        elif media_type == "wallpaper":
            search_folders = [IMAGES_DIR, FAVS_DIR]
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        else:
            search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mkv', '.webm', '.avi', '.mov')
        
        for folder in search_folders:
            if folder.exists():
                folder_files = [
                    f for f in folder.iterdir() 
                    if f.is_file() and f.suffix.lower() in extensions
                ]
                files.extend(folder_files)
        
        return files

    def _get_range_display_name(self):
        range_names = {"all": "All", "wallpaper": "Wallpaper", "mp4": "MP4"}
        return range_names.get(self.current_range, "All")

    def _update_url_input(self, text: str):
        """Update URL input field"""
        if hasattr(self.ui, "urlInput"):
            self.ui.urlInput.setText(text)

    def _set_status(self, message: str):
        """Update status label"""
        if hasattr(self.ui, "statusLabel"):
            self.ui.statusLabel.setText(message)

    def _update_source_buttons_active(self, active_source):
        """Update source button styles"""
        sources = {
            "super": getattr(self.ui, "super_wallpaper_btn", None),
            "favorites": getattr(self.ui, "fvrt_wallpapers_btn", None),
            "added": getattr(self.ui, "added_wallpaper_btn", None)
        }
        
        for btn in sources.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        if active_source in sources and sources[active_source]:
            sources[active_source].setProperty("class", "primary")
            sources[active_source].style().unpolish(sources[active_source])
            sources[active_source].style().polish(sources[active_source])

    def _update_range_buttons_active(self, active_range):
        """Update range button styles"""
        range_buttons = {
            "all": getattr(self.ui, "range_all_bnt", None),
            "wallpaper": getattr(self.ui, "range_wallpaper_bnt", None),
            "mp4": getattr(self.ui, "range_mp4_bnt", None)
        }
        
        for btn in range_buttons.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        if active_range in range_buttons and range_buttons[active_range]:
            range_buttons[active_range].setProperty("class", "primary")
            range_buttons[active_range].style().unpolish(range_buttons[active_range])
            range_buttons[active_range].style().polish(range_buttons[active_range])

    def _perform_reset(self):
        """Reset to default wallpaper"""
        self.controller.stop()
        self.autopause.stop()
        
        if self.previous_wallpaper:
            self.controller.start_image(self.previous_wallpaper)
            self._set_status("Restored previous wallpaper")
        else:
            self._set_status("Reset complete (no previous wallpaper)")

    def _on_download_error(self, error_msg: str):
        """Handle download errors"""
        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        QMessageBox.critical(self, "Download Error", error_msg)
        self._set_status(f"Download failed: {error_msg}")

    # Drag and drop
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if not urls:
            return
        path = urls[0].toLocalFile()
        if path:
            self._set_status(f"Dropped: {Path(path).name}")
            self._apply_input_string(path)

    # CLI handling
    def _handle_cli_args(self):
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            parsed = validate_url_or_path(arg)
            if parsed:
                self._set_status("Applying from URI...")
                self._apply_input_string(parsed)

    # Settings management
    def _load_settings(self):
        """Load saved settings"""
        # Load last video
        last_video = self.config.get_last_video()
        if last_video and hasattr(self.ui, "urlInput"):
            self.ui.urlInput.setText(last_video)

        # Load range preference
        self.current_range = self.config.get_range_preference()
        self.scheduler.set_range(self.current_range)
        self._update_range_buttons_active(self.current_range)

        # Load scheduler settings
        source, interval, enabled = self.config.get_scheduler_settings()
        self.scheduler.source = source
        self.scheduler.interval_minutes = interval
        
        if hasattr(self.ui, "interval_spinBox"):
            self.ui.interval_spinBox.setValue(interval)
        
        if hasattr(self.ui, "enabledCheck"):
            self.ui.enabledCheck.setChecked(enabled)
            if enabled and source:
                self.scheduler.start(source, interval)

    # System tray - FIXED for Ubuntu compatibility
    def _setup_tray(self):
        # CRITICAL: Don't quit when last window is closed
        QApplication.setQuitOnLastWindowClosed(False)
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", "System tray is not available on this system.")
            return
        
        # Create tray icon with proper visibility
        self.tray = QSystemTrayIcon(self)
        
        # Set a proper icon that will be visible
        icon = QIcon()
        cand = Path(__file__).parent.parent / "ui" / "icons" / "logo_biale.svg"
        if cand.exists():
            icon = QIcon(str(cand))
        else:
            # Fallback to a standard icon if custom icon not found
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        
        self.tray.setIcon(icon)
        self.tray.setToolTip("MP4 Wall - Desktop Wallpaper Manager")
        
        # Create context menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_from_tray)
        
        hide_action = QAction("Hide to Tray", self)
        hide_action.triggered.connect(self.hide_to_tray)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self._exit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray.setContextMenu(tray_menu)
        
        # Connect tray icon activation (click/double-click)
        self.tray.activated.connect(self._on_tray_activated)
        
        # Show the tray icon - this is critical for Ubuntu
        self.tray.show()
        
        # Force the icon to be visible
        self.tray.setVisible(True)

    def _on_tray_activated(self, reason):
        """Handle tray icon clicks"""
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click toggles window visibility
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click also toggles window (common on Ubuntu)
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()

    def show_from_tray(self):
        """Show window from system tray"""
        self.show()
        self.raise_()
        self.activateWindow()
        # Ensure window is properly restored
        if self.isMinimized():
            self.showNormal()
        self.is_minimized_to_tray = False

    def hide_to_tray(self):
        """Hide window to system tray with proper notification"""
        self.hide()
        self.is_minimized_to_tray = True
        
        if hasattr(self, 'tray'):
            # Show notification that app is still running
            self.tray.showMessage(
                "MP4 Wall",
                "Application minimized to system tray\nClick the tray icon to restore the window",
                QSystemTrayIcon.Information,
                3000
            )

    def _exit_app(self):
        """Properly quit the application from tray menu"""
        self._perform_reset()
        if hasattr(self, 'tray'):
            self.tray.hide()
        QApplication.quit()