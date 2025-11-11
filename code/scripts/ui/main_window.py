import os
import subprocess
import sys
import random
import shutil
import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStyle, QSizePolicy
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtCore import QTimer, Qt, QEvent, QCoreApplication, QSize

current_dir = os.path.dirname(__file__)
ui_path = os.path.join(current_dir, 'mainUI.py')
sys.path.append(os.path.dirname(current_dir))

try:
    from ui.mainUI import Ui_MainWindow
except ImportError as e:
    logging.error(f"UI import error: {e}")
    try:
        sys.path.append(current_dir)
        from mainUI import Ui_MainWindow
    except ImportError:
        raise ImportError("Cannot import Ui_MainWindow. Make sure mainUI.py exists in the ui folder.")

# Import core modules
from core.wallpaper_controller import WallpaperController
# from core.autopause_controller import AutoPauseController
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



class EnhancedDragDropWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dropped_file_path = None
        self.original_wallpaper = None
        self.parent_app = parent
        self.setup_ui()
    # Function for toggling visibility of buttons and uplaod icon
    def toggle_buttons_visibility(self, visible: bool):
        if visible:
            self.buttons_widget.show()
            self.uploadIcon.hide()
        else:
            self.buttons_widget.hide()
            self.uploadIcon.show()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Drag & drop area
        self.drop_area = QLabel("Drag & drop a photo or video here, or click to choose a file")
        self.drop_area.setAlignment(Qt.AlignCenter)
        self.drop_area.setAcceptDrops(True)
        self.drop_area.dragEnterEvent = self.dragEnterEvent
        self.drop_area.dropEvent = self.dropEvent
        self.drop_area.setMargin(0)
        # change vertical policy to fixed
        self.drop_area.setSizePolicy(self.drop_area.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        
        # Supported formats label
        self.supported_label = QLabel("Supported: JPG, PNG, MP4")
        self.supported_label.setAlignment(Qt.AlignCenter)
        self.supported_label.setMargin(0)
        # change vertical policy to fixed
        self.supported_label.setSizePolicy(self.supported_label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        
        # Action buttons (initially hidden) - CENTERED BUT GROUPED
        self.buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(10, 0, 10, 0)
        
        # Create a container for the buttons to keep them together in center
        button_container = QWidget()
        button_container_layout = QHBoxLayout()
        button_container_layout.setContentsMargins(0, 0, 0, 0)
        button_container_layout.setSpacing(10)  # Space between buttons
        
        # Upload button with icon and primary class
        self.upload_btn = QPushButton(" Set as Wallpaper")
        self.upload_btn.clicked.connect(self.set_as_wallpaper)
        self.upload_btn.setProperty("class", "primary")
        
        # Add upload icon
        self.uploadIcon = QLabel()
        self.uploadIcon.setObjectName(u"uploadIcon")
        self.uploadIcon.setAutoFillBackground(False)
        self.uploadIcon.setPixmap(QPixmap(u":/icons/upload.png"))
        self.uploadIcon.setScaledContents(False)
        self.uploadIcon.setAlignment(Qt.AlignCenter)
        # change vertical policy to fixed
        self.uploadIcon.setSizePolicy(self.uploadIcon.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        self.uploadIcon.setMargin(0)
        
        # Reset button
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_selection)
        self.reset_btn.setProperty("class", "ghost")
        
        # Add reset icon
        reset_icon = QIcon(":/icons/reset.png")
        self.reset_btn.setIcon(reset_icon)
        self.reset_btn.setIconSize(QSize(16, 16))
        
        # Add buttons to container
        button_container_layout.addWidget(self.upload_btn)
        button_container_layout.addWidget(self.reset_btn)
        button_container.setLayout(button_container_layout)
        
        # Center the button container
        buttons_layout.addStretch()
        buttons_layout.addWidget(button_container)
        buttons_layout.addStretch()
        
        self.buttons_widget.setLayout(buttons_layout)
        self.buttons_widget.hide()  # Initially hidden as requested
        
        layout.addWidget(self.uploadIcon)
        layout.addWidget(self.drop_area)
        layout.addWidget(self.supported_label)
        layout.addWidget(self.buttons_widget)
        self.setLayout(layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self.is_valid_wallpaper_file(file_path):
                self.dropped_file_path = file_path
                filename = os.path.basename(file_path)
                self.drop_area.setText(f"Selected: {filename}")
                self.supported_label.hide()
                self.buttons_widget.show()
                self.uploadIcon.hide()
                self.upload_btn.setEnabled(True)
            else:
                self.drop_area.setText("Invalid file type!\nSupported: Images, Videos")
                self.upload_btn.setEnabled(False)
    
    def set_as_wallpaper(self):
        if self.dropped_file_path:
            try:
                # Store current wallpaper before setting new one (only first time)
                if not hasattr(self, 'previous_wallpaper') or not self.previous_wallpaper:
                    self.previous_wallpaper = self.get_current_wallpaper()
                    logging.info(f"Stored original wallpaper: {self.previous_wallpaper}")
                
                # Update URL input field
                if hasattr(self.parent_app, 'ui') and hasattr(self.parent_app.ui, 'urlInput'):
                    self.parent_app.ui.urlInput.setText(self.dropped_file_path)
                
                # Apply the wallpaper
                if self.dropped_file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                    self.parent_app.controller.start_video(self.dropped_file_path)
                else:
                    self.parent_app.controller.start_image(self.dropped_file_path)
                
                # Show success message
                self.drop_area.setText("Wallpaper set successfully!")
                
                # Update status
                if hasattr(self.parent_app, '_set_status'):
                    self.parent_app._set_status(f"Wallpaper set: {os.path.basename(self.dropped_file_path)}")
                
                # Store in config
                self.parent_app.config.set_last_video(self.dropped_file_path)
                
            except Exception as e:
                logging.error(f"Failed to set wallpaper: {e}")
                QMessageBox.critical(self, "Error", f"Failed to set wallpaper: {str(e)}")
    
    def reset_selection(self):
        """Reset to original selection state"""
        self.dropped_file_path = None
        self.drop_area.setText("Drag & drop a photo or video here, or click to choose a file")
        self.supported_label.show()
        self.buttons_widget.hide()
        self.uploadIcon.show()

    def restore_original_wallpaper(self):
        """Restore the original wallpaper that was set before any changes"""
        if hasattr(self, 'previous_wallpaper') and self.previous_wallpaper:
            try:
                logging.info(f"Attempting to restore original wallpaper: {self.previous_wallpaper}")
                
                if os.path.exists(self.previous_wallpaper):
                    if self.previous_wallpaper.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
                        self.parent_app.controller.start_video(self.previous_wallpaper)
                    else:
                        self.parent_app.controller.start_image(self.previous_wallpaper)
                    
                    if hasattr(self.parent_app, '_set_status'):
                        self.parent_app._set_status("Original wallpaper restored")
                    
                    # Update URL input
                    if hasattr(self.parent_app.ui, 'urlInput'):
                        self.parent_app.ui.urlInput.setText(self.previous_wallpaper)
                    
                    logging.info("Original wallpaper restored successfully")
                else:
                    logging.warning(f"Original wallpaper file not found: {self.previous_wallpaper}")
                    self.parent_app._set_status("Original wallpaper file not found")
                    
            except Exception as e:
                logging.error(f"Failed to restore original wallpaper: {e}")
                self.parent_app._set_status("Failed to restore original wallpaper")
    
    def get_current_wallpaper(self):
        """Get the current system wallpaper path"""
        try:
            from utils.system_utils import get_current_desktop_wallpaper
            wallpaper = get_current_desktop_wallpaper()
            logging.info(f"Retrieved current wallpaper: {wallpaper}")
            return wallpaper
        except Exception as e:
            logging.error(f"Could not get current wallpaper: {e}")
        return None
    
    def is_valid_wallpaper_file(self, file_path):
        valid_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', 
                          '.mp4', '.avi', '.mov', '.mkv', '.webm')
        return file_path.lower().endswith(valid_extensions)


class MP4WallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize controllers
        self.controller = WallpaperController()
        # self.autopause = AutoPauseController()
        self.scheduler = WallpaperScheduler()
        self.scheduler.set_change_callback(self._apply_wallpaper_from_path)
        self.config = Config()

        # Enhanced wallpaper state
        self.current_wallpaper_type = None
        self.auto_pause_process = None
        self.last_wallpaper_path = None
        self.current_shuffle_mode = None

        # UI components
        self.fade_overlay = FadeOverlay(self)
        self.fade_overlay.hide()

        # Enhanced drag & drop
        self.drag_drop_widget = EnhancedDragDropWidget(self)

        # State
        self.current_range = "all"
        self.previous_wallpaper = get_current_desktop_wallpaper()
        self.is_minimized_to_tray = False

        # Setup
        self._setup_ui()
        self._setup_tray()
        self._load_settings()
        self._handle_cli_args()
        
        # Setup enhanced features
        self._setup_enhanced_features()
        
        # Ensure status bar is always visible
        self._ensure_status_visible()

    def _ensure_status_visible(self):
        """Make sure status bar is always visible"""
        if hasattr(self.ui, 'bottomFrame'):
            self.ui.bottomFrame.setVisible(True)
            self.ui.bottomFrame.setMinimumHeight(30)  # Force minimum height
            # Remove any styling that might hide it
            self.ui.bottomFrame.setStyleSheet("background-color: transparent;")
        
        if hasattr(self.ui, 'statusLabel'):
            self.ui.statusLabel.setVisible(True)
            self.ui.statusLabel.setText("Ready")
            # Ensure the label has content and size
            self.ui.statusLabel.setMinimumHeight(20)
            self.ui.statusLabel.setStyleSheet("color: white;")  # Make sure text is visible
        
        # Force update
        if hasattr(self.ui, 'bottomFrame'):
            self.ui.bottomFrame.update()
            self.ui.bottomFrame.repaint()

    def _set_status(self, message: str):
        """Update status label and ensure it's visible"""
        if hasattr(self.ui, "statusLabel"):
            self.ui.statusLabel.setText(message)
            self.ui.statusLabel.setVisible(True)
        # Also ensure the parent frame is visible
        if hasattr(self.ui, "bottomFrame"):
            self.ui.bottomFrame.setVisible(True)

    def _setup_enhanced_features(self):
        """Setup the enhanced wallpaper features"""
        # Connect shuffle buttons for mutual exclusivity
        if hasattr(self.ui, 'randomButton') and hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomButton.toggled.connect(self.on_shuffle_wallpaper_toggled)
            self.ui.randomAnimButton.toggled.connect(self.on_shuffle_animation_toggled)
        
        # Connect auto-change checkbox to show/hide interval controls
        if hasattr(self.ui, 'enabledCheck'):
            self.ui.enabledCheck.toggled.connect(self.toggle_interval_controls)
            # Set initial state
            self.toggle_interval_controls(self.ui.enabledCheck.isChecked())

    def on_shuffle_wallpaper_toggled(self, checked):
        """Handle shuffle wallpaper toggle - only non-animated wallpapers"""
        if checked:
            if hasattr(self.ui, 'randomAnimButton'):
                self.ui.randomAnimButton.setChecked(False)
            self.current_shuffle_mode = 'wallpaper'
            logging.info("Shuffle Wallpaper activated - non-animated only")
            
            # Apply first shuffle immediately
            self._apply_shuffled_wallpaper('wallpaper')

    def on_shuffle_animation_toggled(self, checked):
        """Handle shuffle animation toggle - only animated wallpapers"""
        if checked:
            if hasattr(self.ui, 'randomButton'):
                self.ui.randomButton.setChecked(False)
            self.current_shuffle_mode = 'animation'
            logging.info("Shuffle Animation activated - animated only")
            
            # Apply first shuffle immediately
            self._apply_shuffled_wallpaper('animation')

    def toggle_interval_controls(self, enabled):
        """Show/hide interval and range controls based on auto-change setting"""
        interval_controls = [
            'interval_spinBox', 'interval_label', 'interval_value_label',
            'range_label', 'range_combo', 'range_frame'
        ]
        
        for control_name in interval_controls:
            if hasattr(self.ui, control_name):
                control = getattr(self.ui, control_name)
                control.setVisible(enabled)

    def _apply_shuffled_wallpaper(self, shuffle_mode):
        """Apply a shuffled wallpaper based on the current mode"""
        available_wallpapers = self.get_shuffled_wallpapers(shuffle_mode)
        
        if available_wallpapers:
            next_wallpaper = self.ensure_wallpaper_change(available_wallpapers)
            if next_wallpaper:
                self.change_wallpaper_with_optimization(next_wallpaper)
                logging.info(f"Shuffled wallpaper: {os.path.basename(next_wallpaper)}")

    def get_shuffled_wallpapers(self, shuffle_mode):
        """Get appropriate wallpapers based on shuffle mode"""
        if shuffle_mode == 'wallpaper':
            filter_func = self.get_non_animated_filter()
        elif shuffle_mode == 'animation':
            filter_func = self.get_animated_filter()
        else:
            filter_func = lambda x: True  # No filter
        
        all_wallpapers = self._get_media_files("all")  # Use existing method
        filtered_wallpapers = [str(wp) for wp in all_wallpapers if filter_func(str(wp))]
        
        random.shuffle(filtered_wallpapers)
        return filtered_wallpapers

    def get_non_animated_filter(self):
        """Filter for non-animated wallpapers (images)"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        return lambda file_path: any(str(file_path).lower().endswith(ext) for ext in image_extensions)

    def get_animated_filter(self):
        """Filter for animated wallpapers (videos)"""
        video_extensions = {'.mp4', '.webm', '.avi', '.mov', '.mkv'}
        return lambda file_path: any(str(file_path).lower().endswith(ext) for ext in video_extensions)

    def ensure_wallpaper_change(self, available_wallpapers):
        """Ensure wallpaper actually changes, don't select the same one"""
        if len(available_wallpapers) <= 1:
            return available_wallpapers[0] if available_wallpapers else None
            
        # Filter out current wallpaper
        other_wallpapers = [wp for wp in available_wallpapers if wp != self.last_wallpaper_path]
        
        if not other_wallpapers:
            # If all wallpapers are the same as current, still change to force update
            return available_wallpapers[0]
            
        return random.choice(other_wallpapers)

    def change_wallpaper_with_optimization(self, new_wallpaper_path):
        """Optimized wallpaper change with minimal process management"""
        new_wallpaper_type = self.get_wallpaper_type(new_wallpaper_path)
        
        # Determine if process stop is needed
        needs_process_stop = self.needs_process_stop(self.current_wallpaper_type, new_wallpaper_type)
        
        if needs_process_stop:
            self.controller.stop()
        
        # Set new wallpaper using existing method
        self._apply_wallpaper_from_path(Path(new_wallpaper_path))
        self.current_wallpaper_type = new_wallpaper_type
        self.last_wallpaper_path = new_wallpaper_path
        
        # Start autoPause if needed and not already running
        if new_wallpaper_type == 'video' and not self.auto_pause_process:
            self.start_auto_pause_process()

    def needs_process_stop(self, current_type, new_type):
        """
        Determine if we need to stop processes during wallpaper change
        Stop only when: image->video, video->image, or video->video
        Don't stop for: image->image
        """
        if current_type is None:
            return False  # First wallpaper, no need to stop
            
        if current_type == 'image' and new_type == 'image':
            return False  # Image to image transition - no stop needed
            
        return True  # All other transitions need process stop

    def get_wallpaper_type(self, file_path):
        """Determine if wallpaper is image or video"""
        video_extensions = {'.mp4', '.webm', '.avi', '.mov', '.mkv'}
        file_ext = os.path.splitext(file_path)[1].lower()
        return 'video' if file_ext in video_extensions else 'image'

    def start_auto_pause_process(self):
        """Start autoPause.exe and keep it running"""
        try:
            if self.auto_pause_process is None:
                auto_pause_path = self.get_auto_pause_executable()
                self.auto_pause_process = subprocess.Popen([auto_pause_path])
                logging.info("AutoPause process started and will run in background")
        except Exception as e:
            logging.error(f"Failed to start AutoPause process: {e}")

    def stop_auto_pause_process(self):
        """Stop autoPause process only on app close or reset"""
        if self.auto_pause_process:
            try:
                self.auto_pause_process.terminate()
                self.auto_pause_process.wait(timeout=5)
                logging.info("AutoPause process terminated")
            except Exception as e:
                logging.warning(f"Could not terminate AutoPause process: {e}")
            finally:
                self.auto_pause_process = None

    def get_auto_pause_executable(self):
        """Get the path to autoPause executable"""
        # Adjust this path based on your project structure
        app_root = Path(__file__).parent.parent
        auto_pause_path = app_root / "bin" / "autoPause.exe"
        
        if not auto_pause_path.exists():
            # Fallback paths
            auto_pause_path = app_root / "autoPause.exe"
            
        if not auto_pause_path.exists():
            raise FileNotFoundError(f"autoPause.exe not found at {auto_pause_path}")
            
        return str(auto_pause_path)

    # Modified existing methods to use enhanced functionality
    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers ONLY - using enhanced system"""
        if hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomAnimButton.setChecked(True)
        # The actual work is handled by on_shuffle_animation_toggled

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers ONLY - using enhanced system"""
        if hasattr(self.ui, 'randomButton'):
            self.ui.randomButton.setChecked(True)
        # The actual work is handled by on_shuffle_wallpaper_toggled

    def _apply_wallpaper_from_path(self, file_path: Path):
        """Apply wallpaper from file path - OPTIMIZED to avoid unnecessary stops"""
        current_is_video = self.controller.current_is_video
        new_is_video = file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov")
        
        # Use enhanced logic to determine if stop is needed
        current_type = self.current_wallpaper_type or ('video' if current_is_video else 'image')
        new_type = 'video' if new_is_video else 'image'
        needs_stop = self.needs_process_stop(current_type, new_type)
        
        if needs_stop:
            self.controller.stop()
        
        # Start autopause only once for videos using enhanced method
        if new_is_video and not self.auto_pause_process:
            self.start_auto_pause_process()
        
        # Update enhanced state tracking
        self.current_wallpaper_type = new_type
        self.last_wallpaper_path = str(file_path)
        
        # Use existing application logic
        if new_is_video:
            self._apply_video(str(file_path))
        else:
            self._apply_image_with_fade(str(file_path))

    def _perform_reset(self):
        """Reset to default wallpaper - enhanced with process management"""
        self.controller.stop()
        self.autopause.stop()
        self.scheduler.stop()
        
        # Stop autoPause process only on reset
        self.stop_auto_pause_process()
        
        # Reset enhanced state
        self.current_wallpaper_type = None
        self.last_wallpaper_path = None
        self.current_shuffle_mode = None
        
        # Reset shuffle button states
        if hasattr(self.ui, 'randomButton'):
            self.ui.randomButton.setChecked(False)
        if hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomAnimButton.setChecked(False)
        
        # Use the enhanced drag drop widget to restore original wallpaper
        if hasattr(self, 'drag_drop_widget'):
            self.drag_drop_widget.restore_original_wallpaper()
        elif self.previous_wallpaper:
            self.controller.start_image(self.previous_wallpaper)
            self._set_status("Restored previous wallpaper")
        else:
            self._set_status("Reset complete (no previous wallpaper)")

    def cleanup(self):
        """Enhanced cleanup on app close"""
        self.controller.stop()
        self.stop_auto_pause_process()
        logging.info("Application cleanup completed")

    # Rest of your existing methods remain the same...
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and not self.is_minimized_to_tray:
                event.ignore()
                self.hide_to_tray()
        super().changeEvent(event)

    def closeEvent(self, event):
        """
        Handle window close event - Show confirmation dialog before closing
        """
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit Tapeciarnia?\n\nThis will stop all wallpapers and background processes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Stop any running processes WITHOUT reset confirmation
            self._perform_reset()  # Use the version WITHOUT confirmation
            
            # Hide tray icon
            if hasattr(self, 'tray'):
                self.tray.hide()
            
            # Since we set quitOnLastWindowClosed to False, we MUST call quit()
            QApplication.quit()
            
            event.accept()
        else:
            event.ignore()

    def hide_to_tray(self):
        self.hide()
        self.is_minimized_to_tray = True
        if hasattr(self, 'tray'):
            self.tray.showMessage(
                "MP4 Wall",
                "Application is still running in system tray\nClick the tray icon to show the window",
                QSystemTrayIcon.Information,
                3000
            )

    def show_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()
        if self.isMinimized():
            self.showNormal()
        self.is_minimized_to_tray = False


    def _setup_ui(self):
        """Setup UI connections and initial state"""
        self.setAcceptDrops(True)
        
        # Replace the upload area with enhanced drag & drop - FIXED VERSION
        if hasattr(self.ui, 'uploadArea'):
            # Clear existing upload area safely without setParent
            existing_layout = self.ui.uploadArea.layout()
            if existing_layout:
                # Use deleteLater() instead of setParent(None) for thread safety
                for i in reversed(range(existing_layout.count())):
                    layout_item = existing_layout.itemAt(i)
                    if layout_item:
                        widget = layout_item.widget()
                        if widget:
                            widget.deleteLater()  # Thread-safe deletion
                        else:
                            # If it's a layout item without widget, remove it
                            existing_layout.removeItem(layout_item)
            
            # Create new layout if needed
            if not self.ui.uploadArea.layout():
                existing_layout = QVBoxLayout(self.ui.uploadArea)
            
            # Add our enhanced widget
            existing_layout.addWidget(self.drag_drop_widget)
        
        # Center align Start and Reset buttons
        if hasattr(self.ui, 'startButton'):
            self.ui.startButton.setStyleSheet("text-align: center;")
        if hasattr(self.ui, 'resetButton'):
            self.ui.resetButton.setStyleSheet("text-align: center;")
        
        # Connect signals
        self._bind_ui_controls()
        
        # Initial UI state
        self._update_scheduler_ui_state()

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
        
        # if hasattr(self.ui, "resetButton"):
        #     self.ui.resetButton.clicked.connect(self.on_reset_clicked)

        # if hasattr(self.ui, "resetButton"):
        #     self.ui.resetButton.clicked.connect(self._perform_reset)

        if hasattr(self.ui, "resetButton"):
            # Use the version WITH confirmation
            self.ui.resetButton.clicked.connect(self._perform_reset_with_confirmation)

        # Browse button
        if hasattr(self.ui, "browseButton"):
            self.ui.browseButton.clicked.connect(self.on_browse_clicked)

        # Shuffle buttons - only one can be active at a time
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

    def _update_scheduler_ui_state(self):
        """Show/hide interval and range based on scheduler state"""
        enabled = hasattr(self.ui, "enabledCheck") and self.ui.enabledCheck.isChecked()
        
        # Show/hide interval and range controls
        if hasattr(self.ui, "source_n_interval_frame"):
            self.ui.source_n_interval_frame.setVisible(enabled)
        if hasattr(self.ui, "range_frame"):
            self.ui.range_frame.setVisible(enabled)

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
        """Reset to default wallpaper - NOW USES ENHANCED DRAG DROP WIDGET"""
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

    # Shuffle functionality - FIXED: Only one active at a time
    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers ONLY"""
        self.current_shuffle_type = 'animated'
        self._set_status("Shuffling animated wallpapers...")
        
        # Update button states
        self._update_shuffle_button_states('animated')
        
        video_files = self._get_media_files(media_type="mp4")
        
        if not video_files:
            QMessageBox.information(self, "No Videos", 
                                f"No animated wallpapers found in {self._get_range_display_name()} collection.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(video_files)
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers ONLY"""
        self.current_shuffle_type = 'wallpaper'
        self._set_status("Shuffling wallpapers...")
        
        # Update button states
        self._update_shuffle_button_states('wallpaper')
        
        image_files = self._get_media_files(media_type="wallpaper")
        
        if not image_files:
            QMessageBox.information(self, "No Images", 
                                f"No wallpapers found in {self._get_range_display_name()} collection.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(image_files)
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def _update_shuffle_button_states(self, active_type):
        """Update shuffle button states - only one can be active"""
        if hasattr(self.ui, "randomAnimButton"):
            if active_type == 'animated':
                self.ui.randomAnimButton.setProperty("class", "primary")
            else:
                self.ui.randomAnimButton.setProperty("class", "ghost")
            self.ui.randomAnimButton.style().unpolish(self.ui.randomAnimButton)
            self.ui.randomAnimButton.style().polish(self.ui.randomAnimButton)
        
        if hasattr(self.ui, "randomButton"):
            if active_type == 'wallpaper':
                self.ui.randomButton.setProperty("class", "primary")
            else:
                self.ui.randomButton.setProperty("class", "ghost")
            self.ui.randomButton.style().unpolish(self.ui.randomButton)
            self.ui.randomButton.style().polish(self.ui.randomButton)

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
        # Update UI visibility
        self._update_scheduler_ui_state()
        
        if enabled:
            if not self.scheduler.source:
                self.scheduler.source = str(COLLECTION_DIR)
                self._set_status("Scheduler enabled - using entire collection")
            
            interval = self.scheduler.interval_minutes
            if hasattr(self.ui, "interval_spinBox"):
                interval = self.ui.interval_spinBox.value()
            
            self.scheduler.start(self.scheduler.source, interval)
            self._set_status(f"Scheduler started - changing every {interval} minutes")
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
        """Apply wallpaper from file path - OPTIMIZED to avoid unnecessary stops"""
        current_is_video = self.controller.current_is_video
        new_is_video = file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov")
        
        # Only stop if necessary (video to video, video to image, or image to video)
        needs_stop = (current_is_video and new_is_video) or (current_is_video and not new_is_video) or (not current_is_video and new_is_video)
        
        if needs_stop:
            self.controller.stop()
        
        # Start autopause only once for videos
        if new_is_video and not self.autopause.proc:
            self.autopause.start()
        
        if new_is_video:
            self._apply_video(str(file_path))
        else:
            self._apply_image_with_fade(str(file_path))

    def _apply_video(self, video_path: str):
        """Apply video wallpaper"""
        try:
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

    # Utility methods - FIXED: Proper media type separation
    def _get_media_files(self, media_type="all"):
        """Get media files based on current range and media type"""
        files = []
        
        # Define search folders based on current range
        if self.current_range == "mp4":
            search_folders = [VIDEOS_DIR]
        elif self.current_range == "wallpaper":
            search_folders = [IMAGES_DIR]
        else:  # "all"
            search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
        
        # Define extensions based on media type
        if media_type == "mp4":
            extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        elif media_type == "wallpaper":
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        else:
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
        """Reset to default wallpaper WITHOUT confirmation"""
        self.controller.stop()
        self.autopause.stop()
        self.scheduler.stop()
        
        # Stop autoPause process only on reset
        self.stop_auto_pause_process()
        
        # Reset enhanced state
        self.current_wallpaper_type = None
        self.last_wallpaper_path = None
        self.current_shuffle_mode = None
        
        # Reset shuffle button states
        if hasattr(self.ui, 'randomButton'):
            self.ui.randomButton.setChecked(False)
        if hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomAnimButton.setChecked(False)
        
        # Use the enhanced drag drop widget to restore original wallpaper
        if hasattr(self, 'drag_drop_widget'):
            self.drag_drop_widget.restore_original_wallpaper()
        elif self.previous_wallpaper:
            self.controller.start_image(self.previous_wallpaper)
            self._set_status("Restored previous wallpaper")
        else:
            self._set_status("Reset complete (no previous wallpaper)")
        
        # Clear URL input
        if hasattr(self.ui, 'urlInput'):
            self.ui.urlInput.clear()
        
        self._set_status("Reset completed")

    def _perform_reset_with_confirmation(self):
        """Reset to default wallpaper WITH confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Are you sure you want to reset?\n\nThis will stop all current wallpapers and restore the original wallpaper.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._perform_reset()
            self._set_status("Reset completed successfully")
        else:
            self._set_status("Reset cancelled")

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
                self.scheduler.start(self.scheduler.source, interval)
        
        # Update UI state based on scheduler
        self._update_scheduler_ui_state()

    # System tray
    def _setup_tray(self):
        # Don't quit when last window is closed
        QApplication.setQuitOnLastWindowClosed(False)
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", "System tray is not available on this system.")
            return
        
        # Create tray icon
        self.tray = QSystemTrayIcon(self)
        
        # Set icon
        icon = QIcon()
        cand = Path(__file__).parent.parent / "ui" / "icons" / "logo_biale.svg"
        if cand.exists():
            icon = QIcon(str(cand))
        else:
            # Fallback to standard icon
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
        
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
        
        # Connect tray icon activation
        self.tray.activated.connect(self._on_tray_activated)
        
        # Show the tray icon
        self.tray.show()
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
            # Single click also toggles window
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()

    def _exit_app(self):
        """Properly quit the application from tray menu with confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit Tapeciarnia?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Stop any running processes WITHOUT reset confirmation
            self._perform_reset()  # Use the version WITHOUT confirmation
            
            if hasattr(self, 'tray'):
                self.tray.hide()
            QApplication.quit()