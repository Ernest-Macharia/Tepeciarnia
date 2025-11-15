import os
import sys
import random
import logging
import shutil
import logging
from pathlib import Path
import time

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QMessageBox, 
    QSystemTrayIcon, QMenu, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStyle, QSizePolicy, QDialog
)
from PySide6.QtGui import QAction, QIcon, QDragEnterEvent, QDropEvent, QPixmap
from PySide6.QtCore import QTimer, Qt, QEvent, QCoreApplication, QSize,qIsNull, Signal, QThread


current_dir = os.path.dirname(__file__)
ui_path = os.path.join(current_dir, 'mainUI.py')
sys.path.append(os.path.dirname(current_dir))

logger = logging.getLogger(__name__)

try:
    from ui.mainUI import Ui_MainWindow
    logging.info("Successfully imported Ui_MainWindow from ui.mainUI")
except ImportError as e:
    logging.error(f"UI import error: {e}")
    try:
        sys.path.append(current_dir)
        from mainUI import Ui_MainWindow
        logging.info("Successfully imported Ui_MainWindow from local directory")
    except ImportError:
        logging.critical("Cannot import Ui_MainWindow. Make sure mainUI.py exists in the ui folder.")
        raise ImportError("Cannot import Ui_MainWindow. Make sure mainUI.py exists in the ui folder.")

# Import core modules
from core.wallpaper_controller import WallpaperController
from core.download_manager import DownloaderThread
from core.scheduler import WallpaperScheduler
from  core.language_controller import LanguageController
# Import utilities
from utils.path_utils import COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR, get_folder_for_range, get_folder_for_source, open_folder_in_explorer
from utils.system_utils import get_current_desktop_wallpaper
from utils.validators import validate_url_or_path, is_image_url_or_path
from utils.file_utils import download_image, copy_to_collection, cleanup_temp_marker

# Import models
from models.config import Config

# Import UI components
from .widgets import FadeOverlay
from .dialogs import DownloadProgressDialog, ShutdownProgressDialog



class EnhancedDragDropWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        logging.debug("Initializing EnhancedDragDropWidget")
        self.dropped_file_path = None
        self.original_wallpaper = None
        self.parent_app = parent
        self.setup_ui()
        self.update_language()
    
    # Function for toggling visibility of buttons and upload icon
    def toggle_buttons_visibility(self, visible: bool):
        logging.debug(f"Toggling buttons visibility: {visible}")
        if visible:
            self.buttons_widget.show()
            self.uploadIcon.hide()
        else:
            self.buttons_widget.hide()
            self.uploadIcon.show()

    def setup_ui(self):
        logging.debug("Setting up EnhancedDragDropWidget UI")
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Drag & drop area
        self.parent_app.ui.uploadArea.dragEnterEvent = self.dragEnterEvent
        self.parent_app.ui.uploadArea.dropEvent = self.dropEvent
        self.parent_app.ui.uploadArea.dragLeaveEvent = self.dragLeaveEvent
        
        # Upload text
        self.upload_text = QLabel(self.parent_app.lang["uploadSection"]["dragDropInstruction"])
        self.upload_text.setAlignment(Qt.AlignCenter)
        self.upload_text.setAcceptDrops(True)
        self.upload_text.setSizePolicy(self.upload_text.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        
        # Supported formats label
        self.supported_label = QLabel(self.parent_app.lang["uploadSection"]["supportedFormatsHint"])
        self.supported_label.setAlignment(Qt.AlignCenter)
        self.supported_label.setSizePolicy(self.supported_label.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)
        
        # Action buttons (initially hidden)
        self.buttons_widget = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(20, 10, 20, 10)
        buttons_layout.setSpacing(15)
        
        # NEW: Add to Collection button
        self.add_to_collection_btn = QPushButton(self.parent_app.lang["uploadSection"]["addToCollectionButton"])
        self.add_to_collection_btn.clicked.connect(self.add_to_collection)
        self.add_to_collection_btn.setProperty("class", "ghost")
        self.add_to_collection_btn.setMinimumHeight(35)
        
        # NEW: Add to Favorites button  
        self.add_to_favorites_btn = QPushButton(self.parent_app.lang["uploadSection"]["addToFavoritesButton"])
        self.add_to_favorites_btn.clicked.connect(self.add_to_favorites)
        self.add_to_favorites_btn.setProperty("class", "ghost")
        self.add_to_favorites_btn.setMinimumHeight(35)
        
        # Set as Wallpaper button (appears after selecting collection/favorites)
        self.upload_btn = QPushButton(self.parent_app.lang["uploadSection"]["setAsWallpaperButton"])
        self.upload_btn.clicked.connect(self.set_as_wallpaper)
        self.upload_btn.setProperty("class", "primary")
        self.upload_btn.setMinimumHeight(35)
        self.upload_btn.setVisible(False)  # Hidden initially
        
        # Reset button (always visible when file is selected)
        self.reset_btn = QPushButton(self.parent_app.lang["settings"]["resetButton"])
        self.reset_btn.clicked.connect(self.reset_selection)
        self.reset_btn.setProperty("class", "ghost")
        self.reset_btn.setMinimumHeight(35)
        self.reset_btn.setVisible(False)  # Hidden initially

        buttons_layout.addWidget(self.add_to_collection_btn)
        buttons_layout.addWidget(self.add_to_favorites_btn)
        buttons_layout.addWidget(self.upload_btn)
        buttons_layout.addWidget(self.reset_btn)
        
        self.buttons_widget.setLayout(buttons_layout)
        self.buttons_widget.hide()
        
        # Upload icon (initially visible)
        self.uploadIcon = QLabel()
        self.uploadIcon.setPixmap(QPixmap(":/icons/icons/upload.png").scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.uploadIcon.setAlignment(Qt.AlignCenter)
        self.uploadIcon.setStyleSheet("padding:0px;")
        self.uploadIcon.setSizePolicy(self.uploadIcon.sizePolicy().horizontalPolicy(), QSizePolicy.Fixed)

        
        layout.addWidget(self.uploadIcon)
        layout.addWidget(self.upload_text)
        layout.addWidget(self.supported_label)
        layout.addWidget(self.buttons_widget)
        
        self.setLayout(layout)
        logging.debug("EnhancedDragDropWidget UI setup completed")
    
    def update_language(self):
        """Update UI text based on selected language"""
        logging.info("Updating EnhancedDragDropWidget language")
        self.upload_text.setText(self.parent_app.lang["uploadSection"]["dragDropInstruction"])
        self.supported_label.setText(self.parent_app.lang["uploadSection"]["supportedFormatsHint"])
        self.upload_btn.setText(self.parent_app.lang["uploadSection"]["setAsWallpaperButton"])
        self.reset_btn.setText(self.parent_app.lang["settings"]["resetButton"])
    
    def dragEnterEvent(self, event):
        """Check for valid file types when file enters the drop area"""
        logging.debug("Drag enter event in EnhancedDragDropWidget")
        
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                
                # Check if it's a valid wallpaper file type
                if self.is_valid_wallpaper_file(file_path):
                    event.acceptProposedAction()
                    
                    # Visual feedback that this area accepts drops
                    self.setStyleSheet(
                        "background-color: rgba(255, 255, 255, 0.1); border: 0px dashed #4CAF50; border-radius: 5px;")
                    logging.debug(f"Drag event accepted - valid file type: {file_path}")
                else:
                    event.ignore()
                    logging.debug(f"Drag event ignored - invalid file type: {file_path}")
            else:
                event.ignore()
                logging.debug("Drag event ignored - no valid file URLs")
        else:
            event.ignore()
            logging.debug("Drag event ignored - no URLs")

    def dragLeaveEvent(self, event):
        """Handle drag leave event"""
        logging.debug("Drag leave event in EnhancedDragDropWidget")
        # Remove visual feedback
        self.setStyleSheet("")
        super().dragLeaveEvent(event)
    
    def dropEvent(self, event):
        logging.debug("Drop event in EnhancedDragDropWidget")
        # Remove visual feedback
        self.setStyleSheet("")
        
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            logging.info(f"File dropped in drag & drop area: {file_path}")
            if self.is_valid_wallpaper_file(file_path):
                self.dropped_file_path = file_path
                filename = os.path.basename(file_path)
                file_type = "Video" if self.is_video_file(file_path) else "Image"
                
                # Update UI to show file is ready
                self.upload_text.setText(f" {file_type} Ready!\n\n{filename}")
                self.supported_label.hide()
                
                # Show buttons: Add to Collection, Add to Favorites, Reset
                self.toggle_buttons_visibility(True)
                self.uploadIcon.hide()
                
                # Show collection/favorites buttons, hide set as wallpaper initially
                self.add_to_collection_btn.show()
                self.add_to_favorites_btn.show()
                self.upload_btn.hide()  # Hidden until user selects destination
                self.reset_btn.show()   # Always show reset when file is selected
                
                logging.info(f"Valid {file_type.lower()} file selected: {filename}")
                
            else:
                self.upload_text.setText("Invalid file type!\nSupported: Images, Videos")
                self.upload_btn.setEnabled(False)
                logging.warning(f"Invalid file type dropped: {file_path}")
        
        event.acceptProposedAction()

    def add_to_collection(self):
        """Add dropped file to collection"""
        logging.info("Add to Collection button clicked")
        if self.dropped_file_path:
            try:
                self._add_file_to_destination("collection")
                logging.info("File added to collection successfully")
            except Exception as e:
                logging.error(f"Failed to add to collection: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add to collection: {str(e)}")
    
    def add_to_favorites(self):
        """Add dropped file to favorites"""
        logging.info("Add to Favorites button clicked")
        if self.dropped_file_path:
            try:
                self._add_file_to_destination("favorites")
                logging.info("File added to favorites successfully")
            except Exception as e:
                logging.error(f"Failed to add to favorites: {e}")
                QMessageBox.critical(self, "Error", f"Failed to add to favorites: {str(e)}")

    def _add_file_to_destination(self, destination):
        """Add file to specified destination and show set as wallpaper option"""
        if not self.dropped_file_path:
            return
        
        source_path = Path(self.dropped_file_path)
        
        # Determine destination folder
        if destination == "favorites":
            dest_folder = FAVS_DIR
            dest_name = "favorites"
        else:  # collection
            if source_path.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov'):
                dest_folder = VIDEOS_DIR
            else:
                dest_folder = IMAGES_DIR
            dest_name = "collection"
        
        # Copy file with duplicate handling
        dest_path = dest_folder / source_path.name
        counter = 1
        original_stem = source_path.stem
        while dest_path.exists():
            dest_path = dest_folder / f"{original_stem}_{counter}{source_path.suffix}"
            counter += 1
        
        shutil.copy2(source_path, dest_path)
        
        # Store the destination path for potential wallpaper setting
        self.destination_path = str(dest_path)
        
        # Update UI to show success and ask to set as wallpaper
        self.upload_text.setText(f"Added to {dest_name}!\n\n{source_path.name}")
        
        # Hide collection/favorites buttons, show set as wallpaper button
        self.add_to_collection_btn.hide()
        self.add_to_favorites_btn.hide()
        self.upload_btn.show()  # Show set as wallpaper option
        self.reset_btn.show()   # Keep reset visible
        
        # Show success message
        QMessageBox.information(
            self,
            "Success",
            f"File successfully added to {dest_name}!\n\nWould you like to set it as wallpaper now?",
            QMessageBox.StandardButton.Ok
        )
        
        logging.info(f"File added to {dest_name}: {source_path.name} -> {dest_path}")
    
    def set_as_wallpaper(self):
        """Set the added file as wallpaper"""
        logging.info("Set as Wallpaper button clicked")
        if hasattr(self, 'destination_path') and self.destination_path:
            try:
                # Store current wallpaper before setting new one
                if not hasattr(self, 'previous_wallpaper') or not self.previous_wallpaper:
                    self.previous_wallpaper = self.get_current_wallpaper()
                    logging.info(f"Stored original wallpaper: {self.previous_wallpaper}")
                
                # Update URL input field
                if hasattr(self.parent_app, 'ui') and hasattr(self.parent_app.ui, 'urlInput'):
                    self.parent_app.ui.urlInput.setText(self.destination_path)
                
                # Apply the wallpaper
                if self.is_video_file(self.destination_path):
                    logging.info(f"Setting video wallpaper: {self.destination_path}")
                    self.parent_app.controller.start_video(self.destination_path)
                else:
                    logging.info(f"Setting image wallpaper: {self.destination_path}")
                    self.parent_app.controller.start_image(self.destination_path)
                
                # Show success message
                self.upload_text.setText("Wallpaper set successfully!")
                
                # Update status
                if hasattr(self.parent_app, '_set_status'):
                    self.parent_app._set_status(f"Wallpaper set: {os.path.basename(self.destination_path)}")
                
                # Store in config
                self.parent_app.config.set_last_video(self.destination_path)
                logging.info(f"Wallpaper set successfully and saved to config: {os.path.basename(self.destination_path)}")
                
                # Hide buttons after successful set with delay
                QTimer.singleShot(3000, self.reset_selection)
                
            except Exception as e:
                logging.error(f"Failed to set wallpaper: {e}", exc_info=True)
                self.upload_text.setText("Failed to set wallpaper!")
                QMessageBox.critical(self, "Error", f"Failed to set wallpaper: {str(e)}")
        else:
            logging.warning("No destination path available for setting wallpaper")
            QMessageBox.warning(self, "Error", "No file available to set as wallpaper.")
    
    def reset_selection(self):
        """Reset to original selection state"""
        logging.info("Reset selection triggered")
        self.dropped_file_path = None
        if hasattr(self, 'destination_path'):
            delattr(self, 'destination_path')
        self.upload_text.setText(self.parent_app.lang["uploadSection"]["dragDropInstruction"])
        self.supported_label.show()
        self.toggle_buttons_visibility(False)
        self.reset_btn.hide()  # Hide reset when no file selected
        logging.debug("Drag drop widget reset to initial state")
    
    def is_video_file(self, file_path):
        """Check if file is a video"""
        video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
        return file_path.lower().endswith(video_extensions)

    def restore_original_wallpaper(self):
        """Restore the original wallpaper that was set before any changes"""
        logging.info("Restoring original wallpaper")
        if hasattr(self, 'previous_wallpaper') and self.previous_wallpaper:
            try:
                logging.info(f"Attempting to restore original wallpaper: {self.previous_wallpaper}")
                
                if os.path.exists(self.previous_wallpaper):
                    if self.is_video_file(self.previous_wallpaper):
                        logging.info("Restoring original video wallpaper")
                        self.parent_app.controller.start_video(self.previous_wallpaper)
                    else:
                        logging.info("Restoring original image wallpaper")
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
                logging.error(f"Failed to restore original wallpaper: {e}", exc_info=True)
                self.parent_app._set_status("Failed to restore original wallpaper")
    
    def get_current_wallpaper(self):
        """Get the current system wallpaper path"""
        try:
            from utils.system_utils import get_current_desktop_wallpaper
            wallpaper = get_current_desktop_wallpaper()
            logging.info(f"Retrieved current wallpaper: {wallpaper}")
            return wallpaper
        except Exception as e:
            logging.error(f"Could not get current wallpaper: {e}", exc_info=True)
        return None
    
    def is_valid_wallpaper_file(self, file_path):
        """Check if file is a valid wallpaper type with comprehensive validation"""
        valid_extensions = (
            # Images
            '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff',
            # Videos  
            '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v'
        )

        if not file_path or not isinstance(file_path, str):
            logging.debug(f"Invalid file path: {file_path}")
            return False
        
        # Check extension
        file_ext = os.path.splitext(file_path)[1].lower()
        is_valid = file_ext in valid_extensions
        
        logging.debug(f"File validation for {file_path}: {is_valid} (extension: {file_ext})")
        return is_valid
    
class TapeciarniaApp(QMainWindow):
    def __init__(self):
        logging.info("Initializing TapeciarniaApp")
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Initialize controllers
        logging.debug("Initializing controllers")
        self.controller = WallpaperController()
        self.scheduler = WallpaperScheduler()
        self.language_controller = LanguageController()
        self.scheduler.set_change_callback(self._apply_wallpaper_from_path)
        self.config = Config()

        self._set_lang()
        # connect to the language controller signals
        self.language_controller.language_changed.connect(self._update_lang)
        # set initial language

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
        # self._handle_cli_args()
        
        # Setup enhanced features
        self._setup_enhanced_features()
        
        # Ensure status bar is always visible
        self._ensure_status_visible()
        
        logging.info("TapeciarniaApp initialization completed successfully")

    def _update_lang(self, lang:dict):
        """Update UI language based on selected language"""
        self.lang = lang
        # 
        self.update_ui_language()
        self.drag_drop_widget.update_language()

    def _set_lang(self):
        logging.info("Eumarating all language options into combo box")
        self.language_controller.enumerate_languages(self.ui.langCombo)
        # Set initial language
        self.lang = self.language_controller.setup_initial_language(self.ui.langCombo)
        self.update_ui_language()

    def _make_icon(self,icon_name:QIcon,className:str ="primary") -> QIcon:
        if className == "primary":
            icon = QIcon()
            icon.addFile(f":/icons/icons/{icon_name}_blue.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            return icon
        elif className == "ghost":
            icon = QIcon()
            icon.addFile(f":/icons/icons/{icon_name}.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            return icon
        else:
            icon = QIcon()
            icon.addFile(f":/icons/icons/{icon_name}.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
            return icon
 

    def _ensure_status_visible(self):
        """Make sure status bar is always visible"""
        logging.debug("Ensuring status bar visibility")
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
        logging.debug("Status bar visibility ensured")

    def _set_status(self, message: str):
        """Update status label and ensure it's visible"""
        logging.debug(f"Setting status: {message}")
        if hasattr(self.ui, "statusLabel"):
            self.ui.statusLabel.setText(message)
            self.ui.statusLabel.setVisible(True)
        # Also ensure the parent frame is visible
        if hasattr(self.ui, "bottomFrame"):
            self.ui.bottomFrame.setVisible(True)

    def _setup_enhanced_features(self):
        """Setup the enhanced wallpaper features"""
        logging.debug("Setting up enhanced features")
        # Connect shuffle buttons for mutual exclusivity
        if hasattr(self.ui, 'randomButton') and hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomButton.toggled.connect(self.on_shuffle_wallpaper_toggled)
            self.ui.randomAnimButton.toggled.connect(self.on_shuffle_animation_toggled)
            logging.debug("Shuffle buttons connected for mutual exclusivity")
        
        # Connect auto-change checkbox to show/hide interval controls
        if hasattr(self.ui, 'enabledCheck'):
            self.ui.enabledCheck.toggled.connect(self.toggle_interval_controls)
            # Set initial state
            self.toggle_interval_controls(self.ui.enabledCheck.isChecked())
            logging.debug("Auto-change checkbox connected")
        logging.debug("Enhanced features setup completed")

    def on_shuffle_wallpaper_toggled(self, checked):
        """Handle shuffle wallpaper toggle - only non-animated wallpapers"""
        if checked:
            logging.info("Shuffle Wallpaper activated")
            if hasattr(self.ui, 'randomAnimButton'):
                self.ui.randomAnimButton.setChecked(False)
            self.current_shuffle_mode = 'wallpaper'
            logging.info("Shuffle Wallpaper activated - non-animated only")
            
            # Apply first shuffle immediately
            self._apply_shuffled_wallpaper('wallpaper')

    def on_shuffle_animation_toggled(self, checked):
        """Handle shuffle animation toggle - only animated wallpapers"""
        if checked:
            logging.info("Shuffle Animation activated")
            if hasattr(self.ui, 'randomButton'):
                self.ui.randomButton.setChecked(False)
            self.current_shuffle_mode = 'animation'
            logging.info("Shuffle Animation activated - animated only")
            
            # Apply first shuffle immediately
            self._apply_shuffled_wallpaper('animation')

    def toggle_interval_controls(self, enabled):
        """Show/hide interval and range controls based on auto-change setting"""
        logging.debug(f"Toggling interval controls visibility: {enabled}")
        interval_controls = [
            'interval_spinBox', 'interval_label', 'interval_value_label',
            'range_label', 'range_combo', 'range_frame'
        ]
        
        visible_count = 0
        for control_name in interval_controls:
            if hasattr(self.ui, control_name):
                control = getattr(self.ui, control_name)
                control.setVisible(enabled)
                if enabled:
                    visible_count += 1
        
        # Show/hide start button based on scheduler enabled state
        if hasattr(self.ui, 'startButton'):
            self.ui.startButton.setVisible(enabled)
            logging.debug(f"Start button visibility set to: {enabled}")
        
        logging.debug(f"Set {visible_count} interval controls to visible: {enabled}")

    def _apply_shuffled_wallpaper(self, shuffle_mode):
        """Apply a shuffled wallpaper based on the current mode"""
        logging.info(f"Applying shuffled wallpaper in mode: {shuffle_mode}")
        available_wallpapers = self.get_shuffled_wallpapers(shuffle_mode)
        logging.debug(f"Found {len(available_wallpapers)} wallpapers for shuffling")
        
        if available_wallpapers:
            next_wallpaper = self.ensure_wallpaper_change(available_wallpapers)
            if next_wallpaper:
                self.change_wallpaper_with_optimization(next_wallpaper)
                logging.info(f"Shuffled wallpaper applied: {os.path.basename(next_wallpaper)}")
            else:
                logging.warning("No suitable wallpaper found for shuffling")
        else:
            logging.warning("No wallpapers available for shuffling")

    def get_shuffled_wallpapers(self, shuffle_mode):
        """Get appropriate wallpapers based on shuffle mode - from ALL sources"""
        logging.debug(f"Getting shuffled wallpapers for mode: {shuffle_mode} from ALL sources")
        
        if shuffle_mode == 'wallpaper':
            filter_func = self.get_non_animated_filter()
            filter_type = "non-animated (images)"
        elif shuffle_mode == 'animation':
            filter_func = self.get_animated_filter()
            filter_type = "animated (videos)"
        else:
            filter_func = lambda x: True  # No filter
            filter_type = "all"
        
        # Get files from ALL sources (Collection + Favorites)
        all_wallpapers = self._get_media_files("all")
        filtered_wallpapers = [str(wp) for wp in all_wallpapers if filter_func(str(wp))]
        
        logging.debug(f"Filtered {len(filtered_wallpapers)} {filter_type} wallpapers from {len(all_wallpapers)} total across ALL sources")
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
        logging.debug(f"Ensuring wallpaper change from {len(available_wallpapers)} options")
        if len(available_wallpapers) <= 1:
            logging.debug("Only one wallpaper available, no choice needed")
            return available_wallpapers[0] if available_wallpapers else None
            
        # Filter out current wallpaper
        other_wallpapers = [wp for wp in available_wallpapers if wp != self.last_wallpaper_path]
        logging.debug(f"Filtered out current wallpaper, {len(other_wallpapers)} options remain")
        
        if not other_wallpapers:
            # If all wallpapers are the same as current, still change to force update
            logging.debug("All wallpapers are the same as current, forcing change")
            return available_wallpapers[0]
            
        selected = random.choice(other_wallpapers)
        logging.debug(f"Selected new wallpaper: {os.path.basename(selected)}")
        return selected

    def change_wallpaper_with_optimization(self, new_wallpaper_path):
        """Optimized wallpaper change with minimal process management"""
        logging.info(f"Changing wallpaper with optimization: {os.path.basename(new_wallpaper_path)}")
        new_wallpaper_type = self.get_wallpaper_type(new_wallpaper_path)
        logging.debug(f"New wallpaper type: {new_wallpaper_type}")
        
        # Determine if process stop is needed
        needs_process_stop = self.needs_process_stop(self.current_wallpaper_type, new_wallpaper_type)
        logging.debug(f"Process stop needed: {needs_process_stop} (current: {self.current_wallpaper_type}, new: {new_wallpaper_type})")
        
        if needs_process_stop:
            logging.debug("Stopping current wallpaper processes")
            self.controller.stop()
        
        # Set new wallpaper using existing method
        self._apply_wallpaper_from_path(Path(new_wallpaper_path))
        self.current_wallpaper_type = new_wallpaper_type
        self.last_wallpaper_path = new_wallpaper_path
        

    def needs_process_stop(self, current_type, new_type):
        """
        Determine if we need to stop processes during wallpaper change
        Stop only when: image->video, video->image, or video->video
        Don't stop for: image->image
        """
        if current_type is None:
            logging.debug("First wallpaper, no process stop needed")
            return False  # First wallpaper, no need to stop
            
        if current_type == 'image' and new_type == 'image':
            logging.debug("Image to image transition, no process stop needed")
            return False  # Image to image transition - no stop needed
            
        logging.debug(f"Process stop needed for transition: {current_type} -> {new_type}")
        return True  # All other transitions need process stop

    def get_wallpaper_type(self, file_path):
        """Determine if wallpaper is image or video"""
        video_extensions = {'.mp4', '.webm', '.avi', '.mov', '.mkv'}
        file_ext = os.path.splitext(file_path)[1].lower()
        wallpaper_type = 'video' if file_ext in video_extensions else 'image'
        logging.debug(f"File {os.path.basename(file_path)} identified as: {wallpaper_type}")
        return wallpaper_type


    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers ONLY - from ALL sources"""
        logging.info("Shuffle animated triggered - searching ALL sources")
        self.current_shuffle_type = 'animated'
        self._set_status("Shuffling animated wallpapers from all sources...")
        
        # Update button states
        self._update_shuffle_button_states('animated')
        
        # Get videos from ALL sources (Collection + Favorites)
        video_files = self._get_media_files(media_type="mp4")
        logging.debug(f"Found {len(video_files)} animated wallpapers from ALL sources for shuffling")
        
        if not video_files:
            logging.warning("No animated wallpapers found in any source")
            QMessageBox.information(self, "No Videos", 
                                "No animated wallpapers found in your collection or favorites.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(video_files)
        logging.info(f"Selected animated wallpaper from all sources: {selected.name}")
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers ONLY - from ALL sources"""
        logging.info("Shuffle wallpaper triggered - searching ALL sources")
        self.current_shuffle_type = 'wallpaper'
        self._set_status("Shuffling wallpapers from all sources...")
        
        # Update button states
        self._update_shuffle_button_states('wallpaper')
        
        # Get images from ALL sources (Collection + Favorites)
        image_files = self._get_media_files(media_type="wallpaper")
        logging.debug(f"Found {len(image_files)} static wallpapers from ALL sources for shuffling")
        
        if not image_files:
            logging.warning("No static wallpapers found in any source")
            QMessageBox.information(self, "No Images", 
                                "No wallpapers found in your collection or favorites.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(image_files)
        logging.info(f"Selected static wallpaper from all sources: {selected.name}")
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def _apply_wallpaper_from_path(self, file_path: Path):
        """Apply wallpaper from file path - OPTIMIZED to avoid unnecessary stops"""
        logging.info(f"Applying wallpaper from path: {file_path}")
        current_is_video = self.controller.current_is_video
        new_is_video = file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov")
        
        # Use enhanced logic to determine if stop is needed
        current_type = self.current_wallpaper_type or ('video' if current_is_video else 'image')
        new_type = 'video' if new_is_video else 'image'
        needs_stop = self.needs_process_stop(current_type, new_type)
        
        if needs_stop:
            logging.debug("Stopping current wallpaper due to type change")
            self.controller.stop()
        
        
        # Update enhanced state tracking
        self.current_wallpaper_type = new_type
        self.last_wallpaper_path = str(file_path)
        
        # Use existing application logic
        if new_is_video:
            logging.debug("Applying video wallpaper")
            self._apply_video(str(file_path))
        else:
            logging.debug("Applying image wallpaper with fade")
            self._apply_image_with_fade(str(file_path))

    def _perform_reset(self):
        """Reset to default wallpaper WITHOUT confirmation but WITH success message"""
        logging.info("Performing reset without confirmation")
        self.controller.stop()
        self.scheduler.stop()
        
        # Reset enhanced state
        self.current_wallpaper_type = None
        self.last_wallpaper_path = None
        self.current_shuffle_mode = None
        
        # Reset shuffle button states
        if hasattr(self.ui, 'randomButton'):
            self.ui.randomButton.setChecked(False)
            self.ui.randomButton.setProperty("class", "ghost")
            self.ui.randomButton.setIcon(self._make_icon(self.ui.randomButton.property("icon_name"),className="ghost"))
            self.ui.randomButton.style().unpolish(self.ui.randomButton)
            self.ui.randomButton.style().polish(self.ui.randomButton)
        
        if hasattr(self.ui, 'randomAnimButton'):
            self.ui.randomAnimButton.setChecked(False)
            self.ui.randomAnimButton.setProperty("class", "ghost")
            self.ui.randomAnimButton.setIcon(self._make_icon(self.ui.randomAnimButton.property("icon_name"),className="ghost"))
            self.ui.randomAnimButton.style().unpolish(self.ui.randomAnimButton)
            self.ui.randomAnimButton.style().polish(self.ui.randomAnimButton)
        
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
        logging.info("Reset completed successfully")
        
        # Show success confirmation
        QTimer.singleShot(500, self._show_reset_success_message)

    def _show_reset_success_message(self):
        """Show success confirmation dialog after reset"""
        logging.info("Showing reset success confirmation")
        
        # Create a custom dialog for better UX
        success_dialog = QMessageBox(self)
        success_dialog.setWindowTitle(self.lang["dialog"]["reset_success_title"])
        success_dialog.setText(self.lang["dialog"]["reset_success_message"])
        success_dialog.setIcon(QMessageBox.Icon.Information)
        success_dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        
        # Style the dialog to match your app
        success_dialog.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        # Show the dialog
        success_dialog.exec()
        logging.info("Reset success confirmation shown")

    def cleanup(self):
        """Enhanced cleanup on app close"""
        logging.info("Performing application cleanup")
        self.controller.stop()
        self.stop_auto_pause_process()
        logging.info("Application cleanup completed")

    # Rest of your existing methods remain the same...
    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMinimized() and not self.is_minimized_to_tray:
                logging.debug("Window minimize event detected, hiding to tray")
                event.ignore()
                self.hide_to_tray()
        super().changeEvent(event)

    def closeEvent(self, event):
        """
        Handle window close event - Show confirmation dialog before closing
        """
        logging.info("Close event triggered")
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit Tapeciarnia?\n\nThis will stop all wallpapers and background processes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User confirmed exit")
            # Show shutdown progress dialog
            self._show_shutdown_progress(event)
        else:
            logging.info("User cancelled exit")
            event.ignore()

    def _show_shutdown_progress(self, event):
        """Show shutdown progress and perform cleanup"""
        logging.info("Starting shutdown process with enhanced progress dialog")
        
        # Create and show shutdown progress dialog
        self.shutdown_dialog = ShutdownProgressDialog(self)
        self.shutdown_dialog.show()
        
        # Start the actual shutdown process after dialog is shown
        QTimer.singleShot(200, lambda: self._perform_shutdown(event))

    def _perform_shutdown(self, event):
        """Perform shutdown with coordinated progress updates"""
        try:
            logging.info("Performing coordinated shutdown sequence")
            
            # Step 1: Stop wallpaper processes (25%)
            self.shutdown_dialog.update_progress(25, "Stopping wallpaper processes...")
            self.controller.stop()
            QApplication.processEvents()
            
            # Step 2: Stop scheduler (50%)
            self.shutdown_dialog.update_progress(50, "Stopping scheduler...")
            self.scheduler.stop()
            QApplication.processEvents()
            
            # Step 3: Cleanup resources (75%)
            self.shutdown_dialog.update_progress(75, "Cleaning up resources...")
            try:
                if hasattr(self, 'stop_auto_pause_process'):
                    self.stop_auto_pause_process()
            except Exception as e:
                logger.warning(f"Error stopping auto-pause process: {e}")
            QApplication.processEvents()
            
            # Step 4: Save settings (90%)
            self.shutdown_dialog.update_progress(90, "Saving settings...")
            # Add any final settings save operations here
            QApplication.processEvents()
            
            # Step 5: Complete (100%)
            self.shutdown_dialog.update_progress(100, "Shutdown complete!")
            QApplication.processEvents()
            
            # Wait a moment to show completion, then finalize
            QTimer.singleShot(800, lambda: self._finalize_shutdown(event))
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
            # Even if there's an error, try to finalize
            self._finalize_shutdown(event)

    def _finalize_shutdown(self, event):
        """Finalize the shutdown process - FIXED for deleted event"""
        try:
            # Hide tray icon
            if hasattr(self, 'tray'):
                self.tray.hide()
            
            # Close shutdown dialog
            if hasattr(self, 'shutdown_dialog'):
                self.shutdown_dialog.close()
            
            # Don't try to use event if it's already deleted
            try:
                if event and hasattr(event, 'accept'):
                    event.accept()
            except RuntimeError:
                logger.debug("Close event already deleted, continuing shutdown")
            
            # Quit application
            QApplication.quit()
            
            logging.info("Application quit initiated successfully")
            
        except Exception as e:
            logger.error(f"Error finalizing shutdown: {e}", exc_info=True)
            # Force quit if graceful shutdown fails
            QApplication.quit()

    def _show_shutdown_progress_from_tray(self):
        """Show shutdown progress when exiting from tray"""
        logging.info("Starting shutdown process from tray with progress dialog")
        
        # Create and show shutdown progress dialog
        self.shutdown_dialog = ShutdownProgressDialog(self)
        self.shutdown_dialog.show()
        
        # Start shutdown process
        QTimer.singleShot(200, self._perform_shutdown_from_tray)

    def _perform_shutdown_from_tray(self):
        """Perform shutdown from tray with progress updates"""
        try:
            logging.info("Performing shutdown sequence from tray")
            
            # Step 1: Stop wallpaper processes (25%)
            self.shutdown_dialog.update_progress(25, "Stopping wallpaper processes...")
            self.controller.stop()
            QApplication.processEvents()
            
            # Step 2: Stop scheduler (50%)
            self.shutdown_dialog.update_progress(50, "Stopping scheduler...")
            self.scheduler.stop()
            QApplication.processEvents()
            
            # Step 3: Cleanup (75%)
            self.shutdown_dialog.update_progress(75, "Cleaning up resources...")
            try:
                if hasattr(self, 'stop_auto_pause_process'):
                    self.stop_auto_pause_process()
            except Exception as e:
                logger.warning(f"Error stopping auto-pause process: {e}")
            QApplication.processEvents()
            
            # Step 4: Save settings (90%)
            self.shutdown_dialog.update_progress(90, "Saving settings...")
            QApplication.processEvents()
            
            # Step 5: Complete (100%)
            self.shutdown_dialog.update_progress(100, "Shutdown complete!")
            QApplication.processEvents()
            
            # Wait a moment to show completion
            QTimer.singleShot(800, self._finalize_shutdown_from_tray)
            
        except Exception as e:
            logger.error(f"Error during tray shutdown: {e}", exc_info=True)
            self._finalize_shutdown_from_tray()

    def _finalize_shutdown_from_tray(self):
        """Finalize shutdown from tray"""
        try:
            # Hide tray icon
            if hasattr(self, 'tray'):
                self.tray.hide()
            
            # Close shutdown dialog
            if hasattr(self, 'shutdown_dialog'):
                self.shutdown_dialog.close()
            
            # Quit application
            QApplication.quit()
            logging.info("Application quit from tray completed successfully")
            
        except Exception as e:
            logger.error(f"Error finalizing tray shutdown: {e}", exc_info=True)
            QApplication.quit()

    def stop_auto_pause_process(self):
        """Stop any auto-pause background processes"""
        logging.info("Stopping auto-pause processes")
        try:
            if hasattr(self, 'auto_pause_process') and self.auto_pause_process:
                try:
                    self.auto_pause_process.terminate()
                    self.auto_pause_process.wait(2000)  # Wait up to 2 seconds
                    logger.debug("Auto-pause process terminated successfully")
                except Exception as e:
                    logger.warning(f"Could not terminate auto-pause process gracefully: {e}")
                    try:
                        self.auto_pause_process.kill()
                        logger.debug("Auto-pause process killed")
                    except Exception as kill_error:
                        logger.error(f"Could not kill auto-pause process: {kill_error}")
                finally:
                    self.auto_pause_process = None
        except Exception as e:
            logger.warning(f"Error stopping auto-pause process: {e}")

    def hide_to_tray(self):
        logging.info("Hiding window to system tray")
        self.hide()
        self.is_minimized_to_tray = True
        if hasattr(self, 'tray'):
            self.tray.showMessage(
                self.lang["dialog"]["icon_tray_title"],
                self.lang["dialog"]["icon_tray_message"],
                QSystemTrayIcon.Information,
                3000
            )
        logging.debug("Window hidden to tray")

    def show_from_tray(self):
        logging.info("Showing window from system tray")
        self.show()
        self.raise_()
        self.activateWindow()
        if self.isMinimized():
            self.showNormal()
        self.is_minimized_to_tray = False
        logging.debug("Window restored from tray")


    def _setup_ui(self):
        """Setup UI connections and initial state"""
        logging.debug("Setting up UI")
        self.setAcceptDrops(True)
        
        # Replace the upload area with enhanced drag & drop - FIXED VERSION
        if hasattr(self.ui, 'uploadArea'):
            logging.debug("Replacing upload area with enhanced drag drop widget")
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
            logging.debug("Enhanced drag drop widget added to upload area")
        
        
        # Connect signals
        self._bind_ui_controls()
        
        # Initial UI state
        self._update_scheduler_ui_state()
        logging.debug("UI setup completed")

    def on_source_double_clicked(self, source_type):
        """Handle double-click on source buttons to open corresponding folder"""
        logging.info(f"Double-click detected on source: {source_type}")
        folder_path = get_folder_for_source(source_type)
        
        if folder_path.exists():
            success = open_folder_in_explorer(folder_path)
            if success:
                self._set_status(f"Opened {source_type} folder")
                logging.info(f"Successfully opened folder: {folder_path}")
            else:
                self._set_status(f"Failed to open {source_type} folder")
                logging.error(f"Failed to open folder: {folder_path}")
        else:
            logging.warning(f"Folder does not exist: {folder_path}")
            QMessageBox.warning(self, "Folder Not Found", 
                            f"The {source_type} folder does not exist:\n{folder_path}")

    def on_range_double_clicked(self, range_type):
        """Handle double-click on range buttons to open corresponding folder"""
        logging.info(f"Double-click detected on range: {range_type}")
        folder_path = get_folder_for_range(range_type)
        
        if folder_path.exists():
            success = open_folder_in_explorer(folder_path)
            if success:
                self._set_status(f"Opened {range_type} range folder")
                logging.info(f"Successfully opened folder: {folder_path}")
            else:
                self._set_status(f"Failed to open {range_type} folder")
                logging.error(f"Failed to open folder: {folder_path}")
        else:
            logging.warning(f"Folder does not exist: {folder_path}")
            QMessageBox.warning(self, "Folder Not Found", 
                            f"The {range_type} folder does not exist:\n{folder_path}")

    def _bind_ui_controls(self):
        """Bind UI controls to their handlers"""
        logging.debug("Binding UI controls")
        # Main controls
        if hasattr(self.ui, "loadUrlButton"):
            self.ui.loadUrlButton.clicked.connect(self.on_apply_clicked)
            logging.debug("Load URL button connected")
        
        if hasattr(self.ui, "urlInput"):
            self.ui.urlInput.returnPressed.connect(self.on_apply_clicked)
            logging.debug("URL input return pressed connected")

        # Start/Reset buttons (now in Range section)
        if hasattr(self.ui, "startButton"):
            self.ui.startButton.clicked.connect(self.on_start_clicked)
            logging.debug("Start button connected")
        
        if hasattr(self.ui, "resetButton"):
            # Use the version WITH confirmation
            self.ui.resetButton.clicked.connect(self._perform_reset_with_confirmation)
            logging.debug("Reset button connected with confirmation")

        # Browse button
        if hasattr(self.ui, "browseButton"):
            self.ui.browseButton.clicked.connect(self.on_browse_clicked)
            logging.debug("Browse button connected")

        # Shuffle buttons - only one can be active at a time
        if hasattr(self.ui, "randomAnimButton"):
            self.ui.randomAnimButton.clicked.connect(self.on_shuffle_animated)
            logging.debug("Shuffle animated button connected")
        
        if hasattr(self.ui, "randomButton"):
            self.ui.randomButton.clicked.connect(self.on_shuffle_wallpaper)
            logging.debug("Shuffle wallpaper button connected")

        # Source buttons - with double-click support
        if hasattr(self.ui, "super_wallpaper_btn"):
            self.ui.super_wallpaper_btn.clicked.connect(self.on_super_wallpaper)
            self.ui.super_wallpaper_btn.mouseDoubleClickEvent = lambda e: self.on_source_double_clicked("super")
            logging.debug("Super wallpaper button connected")
        
        if hasattr(self.ui, "fvrt_wallpapers_btn"):
            self.ui.fvrt_wallpapers_btn.clicked.connect(self.on_favorite_wallpapers)
            self.ui.fvrt_wallpapers_btn.mouseDoubleClickEvent = lambda e: self.on_source_double_clicked("favorites")
            logging.debug("Favorite wallpapers button connected")
        
        if hasattr(self.ui, "added_wallpaper_btn"):
            self.ui.added_wallpaper_btn.clicked.connect(self.on_added_wallpapers)
            self.ui.added_wallpaper_btn.mouseDoubleClickEvent = lambda e: self.on_source_double_clicked("added")
            logging.debug("Added wallpapers button connected")

        # Range buttons - with double-click support
        if hasattr(self.ui, "range_all_bnt"):
            self.ui.range_all_bnt.clicked.connect(lambda: self.on_range_changed("all"))
            self.ui.range_all_bnt.mouseDoubleClickEvent = lambda e: self.on_range_double_clicked("all")
            logging.debug("Range all button connected")
        
        if hasattr(self.ui, "range_wallpaper_bnt"):
            self.ui.range_wallpaper_bnt.clicked.connect(lambda: self.on_range_changed("wallpaper"))
            self.ui.range_wallpaper_bnt.mouseDoubleClickEvent = lambda e: self.on_range_double_clicked("wallpaper")
            logging.debug("Range wallpaper button connected")
        
        if hasattr(self.ui, "range_mp4_bnt"):
            self.ui.range_mp4_bnt.clicked.connect(lambda: self.on_range_changed("mp4"))
            self.ui.range_mp4_bnt.mouseDoubleClickEvent = lambda e: self.on_range_double_clicked("mp4")
            logging.debug("Range MP4 button connected")

        # Scheduler controls
        if hasattr(self.ui, "enabledCheck"):
            self.ui.enabledCheck.toggled.connect(self.on_scheduler_toggled)
            logging.debug("Scheduler enabled checkbox connected")
        
        if hasattr(self.ui, "interval_spinBox"):
            self.ui.interval_spinBox.valueChanged.connect(self._on_interval_changed)
            logging.debug("Interval spinbox connected")
        
        # connect language combo box
        if hasattr(self.ui, "langCombo"):
            logging.debug("Language combo box connected")
            self.ui.langCombo.currentTextChanged.connect(self.language_controller.on_language_changed)

        if hasattr(self.ui, "logInBnt"):
            self.ui.logInBnt.clicked.connect(self.on_login_clicked)
            logging.debug("Login button connected")

        logging.debug("All UI controls bound successfully")

    def _update_scheduler_ui_state(self):
        """Show/hide interval, range, and start button based on scheduler state"""
        enabled = hasattr(self.ui, "enabledCheck") and self.ui.enabledCheck.isChecked()
        logging.debug(f"Updating scheduler UI state: enabled={enabled}")
        
        # Show/hide interval and range controls
        if hasattr(self.ui, "source_n_interval_frame"):
            self.ui.source_n_interval_frame.setVisible(enabled)
        if hasattr(self.ui, "range_frame"):
            self.ui.range_frame.setVisible(enabled)
        
        # Show/hide start button
        if hasattr(self.ui, "startButton"):
            self.ui.startButton.setVisible(enabled)
            logging.debug(f"Start button visibility: {enabled}")
        
        logging.debug(f"Scheduler UI controls set to visible: {enabled}")

    # Main application methods
    def on_apply_clicked(self):
        """Handle apply/load button click"""
        logging.info("Apply/Load button clicked")
        if not hasattr(self.ui, "urlInput"):
            logging.error("No URL input field available in UI")
            QMessageBox.warning(self, "Error", "No input field available in UI")
            return
        
        url = self.ui.urlInput.text().strip()
        if not url:
            logging.warning("No URL/path provided for apply")
            QMessageBox.warning(self, "Error", "No URL/path provided")
            return
        
        logging.info(f"Applying input string: {url}")
        self._apply_input_string(url)
    def on_start_clicked(self):
        """Start the scheduler with selected settings and random wallpaper"""
        logging.info("Start button clicked - starting scheduler with current settings")
        
        # Check if scheduler is enabled
        if hasattr(self.ui, 'enabledCheck') and not self.ui.enabledCheck.isChecked():
            logging.warning("Scheduler not enabled, enabling it first")
            self.ui.enabledCheck.setChecked(True)
        
        # Get interval from UI
        interval = 30  # default
        if hasattr(self.ui, 'interval_spinBox'):
            interval = self.ui.interval_spinBox.value()
        
        # Get current source and range
        source = self.scheduler.source
        if not source:
            source = str(COLLECTION_DIR)  # default to collection
            self.scheduler.source = source
        
        range_type = self.current_range
        self.scheduler.set_range(range_type)
        
        # Check if there are any files matching the current settings
        logging.info(f"Checking for files with source: {source}, range: {range_type}")
        available_files = self.scheduler._get_media_files()
        
        if not available_files:
            # No files found for current settings - show error popup
            logging.warning(f"No files found for source: {source}, range: {range_type}")
            
            # Determine the error message based on settings
            if source == str(FAVS_DIR):
                if range_type == "mp4":
                    error_msg = "No videos found in your favorites collection!\n\nPlease add some videos to your favorites first."
                elif range_type == "wallpaper":
                    error_msg = "No images found in your favorites collection!\n\nPlease add some images to your favorites first."
                else:  # all
                    error_msg = "No wallpapers found in your favorites collection!\n\nPlease add some wallpapers to your favorites first."
            elif source == str(COLLECTION_DIR):
                if range_type == "mp4":
                    error_msg = "No videos found in your collection!\n\nPlease download or add some videos first."
                elif range_type == "wallpaper":
                    error_msg = "No images found in your collection!\n\nPlease download or add some images first."
                else:  # all
                    error_msg = "No wallpapers found in your collection!\n\nPlease download or add some wallpapers first."
            else:
                error_msg = f"No wallpapers found for current settings!\n\nSource: {source}\nRange: {range_type}"
            
            QMessageBox.warning(
                self,
                "No Wallpapers Found",
                error_msg,
                QMessageBox.StandardButton.Ok
            )
            self._set_status("Scheduler failed - no matching wallpapers")
            return
        
        # Files available - start the scheduler
        logging.info(f"Found {len(available_files)} files for scheduler, starting...")
        self.scheduler.start(source, interval)
        
        # Apply a random wallpaper immediately from the available files
        try:
            random_wallpaper = random.choice(available_files)
            logging.info(f"Applying random wallpaper: {random_wallpaper.name}")
            self._apply_wallpaper_from_path(random_wallpaper)
            self._set_status(f"Scheduler started - {len(available_files)} wallpapers, changing every {interval} minutes")
            
            # Show success message
            QMessageBox.information(
                self,
                "Scheduler Started",
                f"Scheduler started successfully!\n\n"
                f"• Source: {self._get_source_display_name(source)}\n"
                f"• Range: {self._get_range_display_name()}\n"
                f"• Interval: {interval} minutes\n"
                f"• Available wallpapers: {len(available_files)}\n\n"
                f"First wallpaper: {random_wallpaper.name}",
                QMessageBox.StandardButton.Ok
            )
            
        except Exception as e:
            logging.error(f"Failed to apply random wallpaper: {e}")
            self._set_status("Scheduler started but failed to apply first wallpaper")
            QMessageBox.warning(
                self,
                "Scheduler Started with Warning",
                f"Scheduler started but there was an issue applying the first wallpaper:\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def _get_source_display_name(self, source):
        """Get display name for source"""
        source_names = {
            str(FAVS_DIR): "Favorite Wallpapers",
            str(COLLECTION_DIR): "My Collection",
            "super": "Super Wallpaper"
        }
        return source_names.get(source, "Custom Source")

    def _get_range_display_name(self):
        """Get display name for current range"""
        range_names = {
            "all": "All Types",
            "wallpaper": "Images Only", 
            "mp4": "Videos Only"
        }
        return range_names.get(self.current_range, "All Types")


    def on_browse_clicked(self):
        """Browse for local files with enhanced destination selection"""
        logging.info("Browse button clicked")
        path, _ = QFileDialog.getOpenFileName(
            self, "Select video or image", str(Path.home()),
            "Media (*.mp4 *.mkv *.webm *.avi *.mov *.jpg *.jpeg *.png)"
        )
        
        if path:
            logging.info(f"File selected via browse: {path}")
            
            # Show the same interface as drag & drop
            self._handle_browsed_file(path)
        else:
            logging.debug("Browse dialog cancelled")

    def _handle_browsed_file(self, file_path: str):
        """Handle browsed file with destination selection"""
        logging.info(f"Handling browsed file: {file_path}")
        
        if not os.path.exists(file_path):
            logging.error(f"Browsed file does not exist: {file_path}")
            QMessageBox.warning(self, "Error", "Selected file does not exist.")
            return
        
        # Update URL input
        if hasattr(self.ui, 'urlInput'):
            self.ui.urlInput.setText(file_path)
        
        # Show the same interface as drag & drop area
        if hasattr(self, 'drag_drop_widget'):
            # Simulate a file drop in the drag & drop area
            self.drag_drop_widget.dropped_file_path = file_path
            filename = os.path.basename(file_path)
            file_type = "Video" if self.drag_drop_widget.is_video_file(file_path) else "Image"
            
            # Update UI to show file is ready
            self.drag_drop_widget.upload_text.setText(f" {file_type} Ready!\n\n{filename}")
            self.drag_drop_widget.supported_label.hide()
            
            # Show buttons: Add to Collection, Add to Favorites, Reset
            self.drag_drop_widget.toggle_buttons_visibility(True)
            self.drag_drop_widget.uploadIcon.hide()
            
            # Show collection/favorites buttons, hide set as wallpaper initially
            self.drag_drop_widget.add_to_collection_btn.show()
            self.drag_drop_widget.add_to_favorites_btn.show()
            self.drag_drop_widget.upload_btn.hide()  # Hidden until user selects destination
            self.drag_drop_widget.reset_btn.show()   # Always show reset when file is selected
            
            logging.info(f"Browsed file ready for destination selection: {filename}")

    # Shuffle functionality - FIXED: Only one active at a time
    def on_shuffle_animated(self):
        """Shuffle through animated wallpapers ONLY"""
        logging.info("Shuffle animated triggered")
        self.current_shuffle_type = 'animated'
        self._set_status("Shuffling animated wallpapers...")
        
        # Update button states
        self._update_shuffle_button_states('animated')
        
        video_files = self._get_media_files(media_type="mp4")
        logging.debug(f"Found {len(video_files)} animated wallpapers for shuffling")
        
        if not video_files:
            logging.warning(f"No animated wallpapers found in {self._get_range_display_name()} collection")
            QMessageBox.information(self, "No Videos", 
                                f"No animated wallpapers found in {self._get_range_display_name()} collection.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(video_files)
        logging.info(f"Selected animated wallpaper: {selected.name}")
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def on_shuffle_wallpaper(self):
        """Shuffle through static wallpapers ONLY"""
        logging.info("Shuffle wallpaper triggered")
        self.current_shuffle_type = 'wallpaper'
        self._set_status("Shuffling wallpapers...")
        
        # Update button states
        self._update_shuffle_button_states('wallpaper')
        
        image_files = self._get_media_files(media_type="wallpaper")
        logging.debug(f"Found {len(image_files)} static wallpapers for shuffling")
        
        if not image_files:
            logging.warning(f"No static wallpapers found in {self._get_range_display_name()} collection")
            QMessageBox.information(self, "No Images", 
                                f"No wallpapers found in {self._get_range_display_name()} collection.")
            self.current_shuffle_type = None
            self._update_shuffle_button_states(None)
            return
        
        selected = random.choice(image_files)
        logging.info(f"Selected static wallpaper: {selected.name}")
        self._apply_wallpaper_from_path(selected)
        self._update_url_input(str(selected))

    def _update_shuffle_button_states(self, active_type):
        """Update shuffle button states - only one can be active"""
        logging.debug(f"Updating shuffle button states: {active_type}")
        if hasattr(self.ui, "randomAnimButton"):
            if active_type == 'animated':
                self.ui.randomAnimButton.setProperty("class", "primary")
                self.ui.randomAnimButton.setIcon(self._make_icon(self.ui.randomAnimButton.property("icon_name"),className="primary"))
            else:
                self.ui.randomAnimButton.setProperty("class", "ghost")
                self.ui.randomAnimButton.setIcon(self._make_icon(self.ui.randomAnimButton.property("icon_name"),className="ghost"))
            self.ui.randomAnimButton.style().unpolish(self.ui.randomAnimButton)
            self.ui.randomAnimButton.style().polish(self.ui.randomAnimButton)
        
        if hasattr(self.ui, "randomButton"):
            if active_type == 'wallpaper':
                self.ui.randomButton.setProperty("class", "primary")
                self.ui.randomButton.setIcon(self._make_icon(self.ui.randomButton.property("icon_name"),className="primary"))
            else:
                self.ui.randomButton.setProperty("class", "ghost")
                self.ui.randomButton.setIcon(self._make_icon(self.ui.randomButton.property("icon_name"),className="ghost"))
            self.ui.randomButton.style().unpolish(self.ui.randomButton)
            self.ui.randomButton.style().polish(self.ui.randomButton)
        
        logging.debug(f"Shuffle button states updated for: {active_type}")

    # Source selection
    def on_super_wallpaper(self):
        """Super Wallpaper source"""
        logging.info("Super Wallpaper source selected")
        self._set_status("Super Wallpaper source selected")
        QMessageBox.information(self, "Super Wallpaper", 
                            "Super Wallpaper feature - Premium curated wallpapers coming soon!")

    def on_favorite_wallpapers(self):
        """Favorite wallpapers source - ONLY uses FAVS_DIR"""
        logging.info("Favorite wallpapers source selected")
        
        # Check if favorites folder has any files
        if not FAVS_DIR.exists() or not any(FAVS_DIR.iterdir()):
            logging.warning("No favorite wallpapers found")
            QMessageBox.information(
                self, 
                "No Favorites", 
                "No favorite wallpapers found.\n\nAdd some wallpapers to favorites first by:\n"
                "1. Loading a wallpaper from URL or file\n"
                "2. Using the 'Add to Favorites' feature",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Set scheduler to use ONLY FAVS_DIR
        self.scheduler.source = str(FAVS_DIR)
        self._set_status("Favorite wallpapers source selected")
        self._update_source_buttons_active("favorites")
        logging.info("Scheduler set to use FAVS_DIR only")

    def on_added_wallpapers(self):
        """My Collection source - includes ALL folders"""
        logging.info("My Collection source selected")
        self._set_status("My Collection source selected")
        
        has_videos = VIDEOS_DIR.exists() and any(VIDEOS_DIR.iterdir())
        has_images = IMAGES_DIR.exists() and any(IMAGES_DIR.iterdir())
        has_favorites = FAVS_DIR.exists() and any(FAVS_DIR.iterdir())
        
        if not (has_videos or has_images or has_favorites):
            logging.warning("Empty collection - no wallpapers found")
            QMessageBox.information(self, "Empty Collection", 
                                "No wallpapers found in your collection. Download or add some wallpapers first.")
            return
        
        # Set scheduler to use ALL collection folders
        self.scheduler.source = str(COLLECTION_DIR)
        self._set_status("Scheduler set to use entire collection (Videos + Images + Favorites)")
        self._update_source_buttons_active("added")
        logging.info("Scheduler set to use entire collection")

    # Range selection
    def on_range_changed(self, range_type):
        """Handle range selection with validation"""
        logging.info(f"Range changed to: {range_type}")
        self.current_range = range_type
        self.scheduler.set_range(range_type)

        # Check if current source + range combination has files
        if self.scheduler.source:
            available_files = self.scheduler._get_media_files()
            if not available_files:
                # Warn user but don't prevent the change
                logging.warning(f"No files found for source: {self.scheduler.source}, range: {range_type}")
                self._set_status(f"Range set to {range_type} (no files found)")
            else:
                self._set_status(f"Range set to: {range_type} ({len(available_files)} files)")
        else:
            self._set_status(f"Range set to: {range_type}")

        self._update_range_buttons_active(range_type)
        self.config.set_range_preference(range_type)
        logging.debug(f"Range preference saved: {range_type}")

    # Scheduler controls
    def on_scheduler_toggled(self, enabled):
        """Handle scheduler enable/disable"""
        logging.info(f"Scheduler toggled: {enabled}")
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
            logging.info(f"Scheduler started with interval: {interval} minutes")
        else:
            self.scheduler.stop()
            self._set_status("Scheduler stopped")
            logging.info("Scheduler stopped")

    def _on_interval_changed(self, val):
        """Handle interval change"""
        logging.info(f"Interval changed to: {val} minutes")
        self.scheduler.interval_minutes = val
        if self.scheduler.is_active():
            self.scheduler.stop()
            self.scheduler.start(self.scheduler.source, val)
        self._set_status(f"Scheduler interval: {val} min")
    
    def update_ui_language(self):
        self.ui.emailInput.setPlaceholderText(f"{self.lang['auth']['emailPlaceholder']}")
        self.ui.passwordInput.setPlaceholderText(f"{self.lang['auth']['passwordPlaceholder']}")
        self.ui.logInBnt.setText(f"{self.lang['auth']['logInButton']}")
        # main controls
        self.ui.randomAnimButton.setText(f"  {self.lang['navigation']['shuffleAnimatedButton']}")
        self.ui.randomButton.setText(f"  {self.lang['navigation']['shuffleWallpaperButton']}")
        self.ui.browseButton.setText(f"  {self.lang['navigation']['browseWallpapersButton']}")
        # uploadSection
        self.ui.add_file_label.setText(f"  {self.lang['uploadSection']['addFilesHeader']}")
        # self.ui.uploadText.setText(self.lang["uploadSection"]["dragDropInstruction"]) 
        # self.ui.uploadSupported.setText(self.lang["uploadSection"]["supportedFormatsHint"])
        # url loader
        self.ui.url_loader_text_label.setText(f"  {self.lang['uploadSection']['imagesOrVideoURLHeader']}")
        self.ui.loadUrlButton.setText(f"{self.lang['uploadSection']['loadButton']}")
        self.ui.url_helper_text_label.setText(f"  {self.lang['uploadSection']['urlHelperText']}")
        # settings
        self.ui.autoLabel.setText(f"  {self.lang['settings']['autoChangeHeader']}")
        self.ui.enabledCheck.setText(f"  {self.lang['settings']['enabledLabel']}")
        self.ui.inverval_lable.setText(f"  {self.lang['settings']['intervalLabel']}")
        self.ui.wallpaper_source_lable.setText(f"  {self.lang['settings']['wallpaperSourceLabel']}")
        self.ui.super_wallpaper_btn.setText(f"  {self.lang['settings']['superWallpaperButton']}")
        self.ui.fvrt_wallpapers_btn.setText(f"  {self.lang['settings']['favoriteWallpapersButton']}")
        self.ui.added_wallpaper_btn.setText(f"  {self.lang['settings']['myCollectionButton']}")
        self.ui.range_lable.setText(f"  {self.lang['settings']['rangeHeader']}")
        self.ui.range_all_bnt.setText(f"  {self.lang['settings']['rangeAllButton']}")
        self.ui.range_wallpaper_bnt.setText(f"  {self.lang['settings']['rangeWallpaperButton']}")
        self.ui.range_mp4_bnt.setText(f"  {self.lang['settings']['rangeMp4Button']}")
        self.ui.startButton.setText(f"  {self.lang['settings']['startButton']}")
        self.ui.resetButton.setText(f"  {self.lang['settings']['resetButton']}")
            

    # Core wallpaper application logic
    def _apply_input_string(self, text: str):
        """Main method to apply wallpaper from various inputs"""
        logging.info(f"Applying input string: {text}")
        text = (text or "").strip()
        if not text:
            logging.warning("Empty input string provided")
            QMessageBox.warning(self, "Warning", "Please enter a valid URL or file path.")
            return

        validated = validate_url_or_path(text)
        if not validated:
            logging.warning(f"Input not recognized: {text}")
            QMessageBox.warning(self, "Error", f"Input not recognized: {text}")
            return

        # Handle local files
        p = Path(validated)
        if p.exists():
            logging.info(f"Handling local file: {p}")
            self._handle_local_file(p)
            return

        # Handle remote URLs - USING get_media_files
        if validated.lower().startswith("http"):
            logging.info(f"Handling remote URL: {validated}")
            
            media_type = self._get_media_files(validated)
            logging.debug(f"Detected media type: {media_type}")
            
            if media_type == "image":
                logging.info(f"Handling as image URL: {validated}")
                self._handle_remote_image(validated)
            elif media_type == "video":
                logging.info(f"Handling as video URL: {validated}")
                self._handle_remote_video(validated)
            else:
                logging.warning(f"Unsupported URL type: {validated}")
                QMessageBox.warning(self, "Unsupported URL", 
                                "The URL doesn't appear to be a supported image or video.")
            return

        logging.warning(f"Unsupported input type: {text}")
        QMessageBox.warning(self, "Invalid Input", "Unsupported input type.")

    def _handle_local_file(self, file_path: Path):
        """Handle local file application"""
        logging.info(f"Processing local file: {file_path}")
        if file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov"):
            logging.debug("Local file is video, copying to videos directory")
            dest = copy_to_collection(file_path, VIDEOS_DIR)
            self._apply_video(str(dest))
        elif file_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".bmp", ".gif"):
            logging.debug("Local file is image, copying to images directory")
            dest = copy_to_collection(file_path, IMAGES_DIR)
            self._apply_image_with_fade(str(dest))
        else:
            logging.warning(f"Unsupported local file type: {file_path.suffix}")
            QMessageBox.warning(self, "Unsupported", "Unsupported local file type.")

    def _handle_remote_image(self, url: str):
        """Handle remote image download and application"""
        logging.info(f"Downloading remote image: {url}")
        self._set_status("Downloading image...")
        try:
            local_path = download_image(url)
            self._apply_image_with_fade(local_path)
            self.config.set_last_video(local_path)
            self._set_status(f"Image saved to collection: {Path(local_path).name}")
            logging.info(f"Remote image downloaded successfully: {local_path}")
        except Exception as e:
            logging.error(f"Failed to download image: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to download image: {e}")

    def _handle_remote_video(self, url: str):
        """Handle remote video download - FIXED for direct video links"""
        logging.info(f"Downloading remote video: {url}")
        self._set_status("Downloading video...")
        cleanup_temp_marker()

        # Check if it's a direct video link (ends with common video extensions)
        direct_video_extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        is_direct_link = any(url.lower().endswith(ext) for ext in direct_video_extensions)
        
        if is_direct_link:
            logging.info(f"Detected direct video link: {url}")
            self._handle_direct_video_download(url)
        else:
            logging.info(f"Using yt-dlp for video URL: {url}")
            self._handle_ytdlp_video_download(url)

    def _handle_direct_video_download(self, url: str):
        """Handle direct video file downloads (not YouTube/streaming)"""
        try:
            import requests
            from urllib.parse import urlparse
            
            logging.info(f"Starting direct video download: {url}")
            
            # Create progress dialog
            self.progress_dialog = DownloadProgressDialog(self)
            self.progress_dialog.show()
            self.progress_dialog.update_progress(0, "Starting direct download...")
            
            # Get filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename or '.' not in filename:
                filename = f"video_{int(time.time())}.mp4"
            
            # Sanitize filename
            filename = self._get_safe_filename(filename)
            download_path = VIDEOS_DIR / filename
            
            logging.info(f"Downloading to: {download_path}")
            
            # Start download in a thread to avoid blocking UI
            self.direct_download_thread = DirectDownloadThread(url, str(download_path))
            self.direct_download_thread.progress.connect(
                lambda percent, status: (
                    self.progress_dialog.update_progress(percent, status),
                    self._set_status(status)
                )
            )
            self.direct_download_thread.error.connect(self._on_download_error)
            self.direct_download_thread.done.connect(self._on_direct_download_done)
            
            self.direct_download_thread.start()
            logging.info("Direct download thread started")
            
        except Exception as e:
            logging.error(f"Direct download setup failed: {e}", exc_info=True)
            if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
                self.progress_dialog.close()
            QMessageBox.critical(self, "Error", f"Download setup failed: {e}")

    def _handle_ytdlp_video_download(self, url: str):
        """Handle YouTube/streaming video downloads using yt-dlp"""
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
            logging.info("YouTube downloader thread started")

        except Exception as e:
            logging.error(f"YouTube download setup failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Download setup failed: {e}")

    def _on_direct_download_done(self, file_path: str):
        """Handle completion of direct video download - FIXED to not set wallpaper on failure"""
        logging.info(f"Direct download completed: {file_path}")
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        
        # Check if download actually succeeded
        if not file_path or not os.path.exists(file_path):
            logger.error("Direct download failed - file not found")
            self._set_status("Direct download failed - file not found")
            # Don't set any wallpaper
            return
        
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error("Direct download failed - file is empty")
            self._set_status("Direct download failed - empty file")
            # Don't set any wallpaper
            return
            
        logging.info(f"Direct download successful: {file_path}")
        self._apply_wallpaper_from_path(Path(file_path))
        self._set_status(f"Video downloaded and set: {os.path.basename(file_path)}")

    def _get_safe_filename(self, filename):
        """Remove invalid characters for both Windows and Linux"""
        logging.debug(f"Sanitizing filename: {filename}")
        # Characters invalid on Windows: < > : " | ? *
        # Characters to avoid on Linux: / and null bytes
        invalid_chars = '<>:"|?*/\0'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        logging.debug(f"Sanitized filename: {filename}")
        return filename

    def _on_download_done(self, path: str):
        """Handle download completion with robust validation"""
        logging.info(f"Download completion handler called with path: {path}")
        
        # Close progress dialog first
        if hasattr(self, 'progress_dialog') and self.progress_dialog.isVisible():
            self.progress_dialog.close()
            logging.debug("Progress dialog closed")
        
        # Validate the downloaded file thoroughly
        if not self._validate_downloaded_file(path):
            logging.error(f"Download validation failed for: {path}")
            self._set_status("Download failed - file validation error")
            return
        
        # Only proceed if file is valid
        p = Path(path)
        logging.info(f"Download validated successfully: {p.name} ({p.stat().st_size} bytes)")
        
        # Ask user where to add the file
        self._ask_download_destination(p)

    def _validate_downloaded_file(self, path: str) -> bool:
        """Thoroughly validate the downloaded file"""
        if not path or not isinstance(path, str):
            logging.error("Invalid path provided")
            return False
        
        try:
            p = Path(path)
            
            # Check if file exists
            if not p.exists():
                logging.error(f"Downloaded file does not exist: {path}")
                return False
            
            # Check file size
            file_size = p.stat().st_size
            if file_size == 0:
                logging.error(f"Downloaded file is empty: {path}")
                return False
            
            # Check if file is readable
            if not os.access(p, os.R_OK):
                logging.error(f"Downloaded file is not readable: {path}")
                return False
            
            # Additional checks for video files
            if p.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov'):
                # Quick check if it might be a valid video file
                if file_size < 1024:  # Less than 1KB is suspicious for a video
                    logging.warning(f"Video file seems too small: {file_size} bytes")
                    # Don't fail here, just warn
            
            logging.info(f"File validation passed: {p.name} ({file_size} bytes)")
            return True
            
        except Exception as e:
            logging.error(f"File validation error: {e}")
            return False

    def _ask_download_destination(self, downloaded_file: Path):
        """Ask user where to add downloaded file with error handling"""
        logging.info("Asking user for download destination")
        
        # Double-check file still exists before showing dialog
        if not downloaded_file.exists():
            logging.error("Downloaded file disappeared before destination selection")
            QMessageBox.critical(
                self,
                "File Error",
                "The downloaded file is no longer available. Please try downloading again.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Add Downloaded File")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)
            
            layout = QVBoxLayout(dialog)
            
            # Message with file info
            file_size = downloaded_file.stat().st_size
            message = QLabel(
                f"Where would you like to add the downloaded file?\n\n"
                f"{downloaded_file.name}\n"
                f"Size: {file_size / 1024 / 1024:.1f} MB"
            )
            message.setAlignment(Qt.AlignCenter)
            layout.addWidget(message)
            
            # Buttons
            buttons_layout = QHBoxLayout()
            
            add_to_collection_btn = QPushButton("Add to Collection")
            add_to_favorites_btn = QPushButton("Add to Favorites")
            cancel_btn = QPushButton("Cancel")
            
            add_to_collection_btn.clicked.connect(
                lambda: self._safe_process_destination(downloaded_file, "collection", dialog)
            )
            add_to_favorites_btn.clicked.connect(
                lambda: self._safe_process_destination(downloaded_file, "favorites", dialog)
            )
            cancel_btn.clicked.connect(dialog.reject)
            
            buttons_layout.addWidget(add_to_collection_btn)
            buttons_layout.addWidget(add_to_favorites_btn)
            buttons_layout.addWidget(cancel_btn)
            
            layout.addLayout(buttons_layout)
            
            dialog.exec()
            
        except Exception as e:
            logging.error(f"Error showing destination dialog: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to show destination options: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def _safe_process_destination(self, downloaded_file: Path, destination: str, dialog: QDialog):
        """Safely process destination with comprehensive error handling"""
        try:
            # Final validation before processing
            if not downloaded_file.exists():
                logging.error("File disappeared during destination selection")
                QMessageBox.critical(
                    self,
                    "File Error", 
                    "The file is no longer available. Operation cancelled.",
                    QMessageBox.StandardButton.Ok
                )
                dialog.reject()
                return
            
            self._process_download_destination(downloaded_file, destination, dialog)
            
        except Exception as e:
            logging.error(f"Error processing destination: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to process file: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
            dialog.reject()

    def _process_download_destination(self, downloaded_file: Path, destination: str, dialog: QDialog):
        """Process the downloaded file to specified destination"""
        try:
            # Determine destination folder
            if destination == "favorites":
                dest_folder = FAVS_DIR
                dest_name = "favorites"
            else:  # collection
                if downloaded_file.suffix.lower() in ('.mp4', '.mkv', '.webm', '.avi', '.mov'):
                    dest_folder = VIDEOS_DIR
                else:
                    dest_folder = IMAGES_DIR
                dest_name = "collection"
            
            # Copy file with duplicate handling
            dest_path = dest_folder / downloaded_file.name
            counter = 1
            original_stem = downloaded_file.stem
            while dest_path.exists():
                dest_path = dest_folder / f"{original_stem}_{counter}{downloaded_file.suffix}"
                counter += 1
            
            shutil.copy2(downloaded_file, dest_path)
            
            # Close the destination dialog
            dialog.accept()
            
            # Ask if user wants to set as wallpaper
            self._ask_set_as_wallpaper(dest_path, dest_name)
            
            logging.info(f"Downloaded file added to {dest_name}: {dest_path}")
            
        except Exception as e:
            logging.error(f"Failed to process download destination: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add file: {str(e)}")
            dialog.reject()

    def _ask_set_as_wallpaper(self, file_path: Path, source: str):
        """Ask user if they want to set the file as wallpaper"""
        logging.info(f"Asking to set as wallpaper: {file_path}")
        
        reply = QMessageBox.question(
            self,
            "Set as Wallpaper?",
            f"File successfully added to {source}!\n\n"
            f"Would you like to set '{file_path.name}' as your wallpaper now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logging.info(f"User chose to set as wallpaper: {file_path}")
            self._apply_wallpaper_from_path(file_path)
            self._set_status(f"Wallpaper set: {file_path.name}")
            QMessageBox.information(
                self,
                "Success",
                f"Wallpaper set successfully!\n\n{file_path.name}",
                QMessageBox.StandardButton.Ok
            )
        else:
            logging.info(f"User chose not to set as wallpaper: {file_path}")
            self._set_status(f"File added to {source}: {file_path.name}")
            # Still update URL input so user can set it later
            if hasattr(self.ui, 'urlInput'):
                self.ui.urlInput.setText(str(file_path))

    def _apply_wallpaper_from_path(self, file_path: Path):
        """Apply wallpaper from file path - OPTIMIZED to avoid unnecessary stops"""
        logging.info(f"Applying wallpaper from path: {file_path}")
        current_is_video = self.controller.current_is_video
        new_is_video = file_path.suffix.lower() in (".mp4", ".mkv", ".webm", ".avi", ".mov")
        
        # Only stop if necessary (video to video, video to image, or image to video)
        needs_stop = (current_is_video and new_is_video) or (current_is_video and not new_is_video) or (not current_is_video and new_is_video)
        # No need to stop here, as the controller methods handle it
        # if needs_stop:
        #     logging.debug("Stopping current wallpaper due to type change")
        #     self.controller.stop()
        
        if new_is_video:
            self._apply_video(str(file_path))
        else:
            self._apply_image_with_fade(str(file_path))

    def _apply_video(self, video_path: str):
        """Apply video wallpaper"""
        try:
            logging.info(f"Applying video wallpaper: {video_path}")
            self.controller.start_video(video_path)
            self.config.set_last_video(video_path)
            self._set_status(f"Playing video: {Path(video_path).name}")
            self._update_url_input(video_path)
            logging.info(f"Video wallpaper applied successfully: {Path(video_path).name}")
        except Exception as e:
            logging.error(f"Failed to play video: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to play video: {e}")

    def _apply_image_with_fade(self, image_path: str):
        """Apply image wallpaper with fade effect - FIXED for null pixmap"""
        try:
            logging.info(f"Applying image wallpaper with fade: {image_path}")
            
            # Check if image file exists and is valid
            if not os.path.exists(image_path):
                logger.error(f"Image file does not exist: {image_path}")
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Load the new pixmap first
            new_pix = QPixmap(image_path)
            if new_pix.isNull():
                logger.error(f"Failed to load image: {image_path}")
                raise ValueError(f"Invalid image file: {image_path}")
            
            # Scale the new pixmap
            new_pix = new_pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            # Try to get old pixmap, but continue if it fails
            old_pix = None
            try:
                old_pix = self.grab()
                if old_pix.isNull():
                    logger.debug("Old pixmap is null, using default fade")
                    old_pix = None
            except Exception as e:
                logger.debug(f"Could not grab old pixmap: {e}")
                old_pix = None
            
            # Setup fade overlay
            self.fade_overlay.set_pixmaps(old_pix, new_pix)
            self.fade_overlay.show()
            self.fade_overlay.raise_()
            self.fade_overlay.animate_to(duration=650)
            
            # Apply wallpaper
            self.controller.start_image(image_path)
            self.config.set_last_video(image_path)
            
            # Hide overlay after animation
            QTimer.singleShot(700, self.fade_overlay.hide)
            self._set_status(f"Image applied: {Path(image_path).name}")
            self._update_url_input(image_path)
            logging.info(f"Image wallpaper applied with fade: {Path(image_path).name}")
            
        except Exception as e:
            logger.error(f"Fade apply failed: {e}", exc_info=True)
            # Fallback to direct application without fade
            try:
                logging.info("Attempting direct image application without fade")
                self.controller.start_image(image_path)
                self.config.set_last_video(image_path)
                self._set_status(f"Image applied (no fade): {Path(image_path).name}")
                self._update_url_input(image_path)
            except Exception as fallback_error:
                logger.error(f"Fallback image application also failed: {fallback_error}")
                QMessageBox.warning(self, "Error", f"Failed to apply image: {fallback_error}")

    # Utility methods - FIXED: Proper media type separation
    def _get_media_files(self, media_type="all"):
        """Get media files based on current range and media type - FIXED LOGIC"""
        logging.debug(f"Getting media files - type: {media_type}, range: {self.current_range}")
        files = []
        
        # Define search folders based on CURRENT SOURCE (not just range)
        if hasattr(self, 'scheduler') and self.scheduler.source:
            if self.scheduler.source == str(FAVS_DIR):
                search_folders = [FAVS_DIR]
                source_type = "favorites"
            elif self.scheduler.source == str(COLLECTION_DIR):
                search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
                source_type = "collection"
            else:
                search_folders = [Path(self.scheduler.source)]
                source_type = "custom"
        else:
            # Fallback to range-based selection
            if self.current_range == "mp4":
                search_folders = [VIDEOS_DIR]
            elif self.current_range == "wallpaper":
                search_folders = [IMAGES_DIR]
            else:  # "all"
                search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
            source_type = "range-based"
        
        logging.debug(f"Using source: {source_type}, folders: {[str(f) for f in search_folders]}")
        
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
                logging.debug(f"Found {len(folder_files)} files in {folder}")
        
        logging.debug(f"Total media files found: {len(files)} from {source_type}")
        return files

    def _get_range_display_name(self):
        range_names = {"all": "All", "wallpaper": "Wallpaper", "mp4": "MP4"}
        display_name = range_names.get(self.current_range, "All")
        logging.debug(f"Range display name: {display_name}")
        return display_name

    def _update_url_input(self, text: str):
        """Update URL input field"""
        logging.debug(f"Updating URL input field: {text}")
        if hasattr(self.ui, "urlInput"):
            self.ui.urlInput.setText(text)

    def _update_source_buttons_active(self, active_source):
        """Update source button styles"""
        logging.debug(f"Updating source button styles for: {active_source}")
        sources = {
            "super": getattr(self.ui, "super_wallpaper_btn", None),
            "favorites": getattr(self.ui, "fvrt_wallpapers_btn", None),
            "added": getattr(self.ui, "added_wallpaper_btn", None)
        }
        
        for btn in sources.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.setIcon(self._make_icon(btn.property("icon_name"),className="ghost"))
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        if active_source in sources and sources[active_source]:
            sources[active_source].setProperty("class", "primary")
            sources[active_source].setIcon(self._make_icon(sources[active_source].property("icon_name"),className="primary"))
            sources[active_source].style().unpolish(sources[active_source])
            sources[active_source].style().polish(sources[active_source])
        
        logging.debug(f"Source button {active_source} set to active")

    def _update_range_buttons_active(self, active_range):
        """Update range button styles"""
        logging.debug(f"Updating range button styles for: {active_range}")
        range_buttons = {
            "all": getattr(self.ui, "range_all_bnt", None),
            "wallpaper": getattr(self.ui, "range_wallpaper_bnt", None),
            "mp4": getattr(self.ui, "range_mp4_bnt", None)
        }
        
        for btn in range_buttons.values():
            if btn:
                btn.setProperty("class", "ghost")
                btn.setIcon(self._make_icon(btn.property("icon_name"),className="ghost"))
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        
        if active_range in range_buttons and range_buttons[active_range]:
            range_buttons[active_range].setProperty("class", "primary")
            range_buttons[active_range].setIcon(self._make_icon(range_buttons[active_range].property("icon_name"),className="primary"))
            range_buttons[active_range].style().unpolish(range_buttons[active_range])
            range_buttons[active_range].style().polish(range_buttons[active_range])
        
        logging.debug(f"Range button {active_range} set to active")

    def _perform_reset_with_confirmation(self):
        """Reset to default wallpaper WITH confirmation"""
        logging.info("Reset with confirmation triggered")
        reply = QMessageBox.question(
            self,
            self.lang["dialog"]["confirm_reset_title"],
            self.lang["dialog"]["confirm_reset_dia"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User confirmed reset")
            self._perform_reset()
            self._set_status("Reset completed successfully")
        else:
            logging.info("User cancelled reset")
            self._set_status("Reset cancelled")

    def _on_download_error(self, error_msg: str):
        """Handle download errors"""
        logging.error(f"Download error: {error_msg}")
        if hasattr(self, "progress_dialog") and self.progress_dialog.isVisible():
            self.progress_dialog.close()
        QMessageBox.critical(self, "Download Error", error_msg)
        self._set_status(f"Download failed: {error_msg}")

    # Drag and drop
    # def dragEnterEvent(self, e: QDragEnterEvent):
    #     if e.mimeData().hasUrls():
    #         e.acceptProposedAction()
    #         logging.debug("Drag enter event accepted")
    #     else:
    #         e.ignore()
    #         logging.debug("Drag enter event ignored - no URLs")

    # def dropEvent(self, e: QDropEvent):
    #     urls = e.mimeData().urls()
    #     if not urls:
    #         logging.debug("Drop event ignored - no URLs")
    #         return
    #     path = urls[0].toLocalFile()
    #     if path:
    #         logging.info(f"File dropped on main window: {path}")
    #         self._set_status(f"Dropped: {Path(path).name}")
    #         self._apply_input_string(path)

    # CLI handling
    # def _handle_cli_args(self):
    #     if len(sys.argv) > 1:
    #         arg = sys.argv[1]
    #         logging.info(f"Processing CLI argument: {arg}")
    #         parsed = validate_url_or_path(arg)
    #         if parsed:
    #             self._set_status("Applying from URI...")
    #             self._apply_input_string(parsed)
    #             logging.info("CLI argument processed successfully")
    #         else:
    #             logging.warning(f"Invalid CLI argument: {arg}")
    #     else:
            # logging.debug("No CLI arguments provided")

    # Settings management
    def _load_settings(self):
        """Load saved settings"""
        logging.info("Loading saved settings")
        # Load last video
        last_video = self.config.get_last_video()
        if last_video and hasattr(self.ui, "urlInput"):
            self.ui.urlInput.setText(last_video)
            logging.info(f"Loaded last video from config: {last_video}")

        # Load range preference
        self.current_range = self.config.get_range_preference()
        self.scheduler.set_range(self.current_range)
        self._update_range_buttons_active(self.current_range)
        logging.info(f"Loaded range preference: {self.current_range}")

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
        
        logging.info(f"Loaded scheduler settings - source: {source}, interval: {interval}, enabled: {enabled}")
        
        # Update UI state based on scheduler
        self._update_scheduler_ui_state()
        logging.info("Settings loaded successfully")

    # System tray
    def _setup_tray(self):
        logging.debug("Setting up system tray")
        # Don't quit when last window is closed
        QApplication.setQuitOnLastWindowClosed(False)
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logging.error("System tray is not available on this system")
            QMessageBox.critical(None, "System Tray", "System tray is not available on this system.")
            return
        
        # Create tray icon
        self.tray = QSystemTrayIcon(self)
        
        # Set icon
        icon = QIcon()
        cand = Path(__file__).parent.parent / "bin" / "media" / "icon.ico"
        if cand.exists():
            icon = QIcon(str(cand))
            logging.debug("Using custom tray icon")
        else:
            # Fallback to standard icon
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)
            logging.debug("Using fallback system tray icon")
        
        self.tray.setIcon(icon)
        self.tray.setToolTip("Tapeciarnia - Desktop Wallpaper Manager")
        
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
        logging.info("System tray setup completed")

    def _on_tray_activated(self, reason):
        """Handle tray icon clicks"""
        logging.debug(f"Tray icon activated with reason: {reason}")
        if reason == QSystemTrayIcon.DoubleClick:
            # Double-click toggles window visibility
            logging.debug("Tray icon double-clicked")
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()
        elif reason == QSystemTrayIcon.Trigger:
            # Single click also toggles window
            logging.debug("Tray icon single-clicked")
            if self.isVisible():
                self.hide_to_tray()
            else:
                self.show_from_tray()
    
    def on_login_clicked(self):
        """Handle login button click - show Coming Soon message"""
        logging.info("Login button clicked - showing coming soon message")
        
        QMessageBox.information(
            self,
            "Coming Soon",
            "Login functionality will be available in a future update!\n\n"
            "For now, enjoy all the wallpaper features without an account.",
            QMessageBox.StandardButton.Ok
        )

    def _exit_app(self):
        """Properly quit the application from tray menu with confirmation and progress"""
        logging.info("Exit from tray menu triggered")
        reply = QMessageBox.question(
            self,
            self.lang["dialog"]["confirm_exit_title"],
            self.lang["dialog"]["confirm_exit_dialog"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            logging.info("User confirmed exit from tray")
            # Show shutdown progress for tray exit too
            self._show_shutdown_progress_from_tray()
        else:
            logging.info("User cancelled exit from tray")

    def handle_startup_uri(self, action, params):
        """
        Processes the URI command received upon application launch.
        
        Args:
            action (str): The primary command (e.g., 'setwallpaper').
            params (dict): Dictionary of query parameters (e.g., {'url': 'http://...'}).
        """
        logging.info(f"Handling startup URI. Action: {action}, Params: {params}")

        if action == "setwallpaper":
            if 'url' in params:
                wallpaper_url = params['url']
                logging.info(f"Executing setwallpaper command for URL: {wallpaper_url}")

                
                # Show a confirmation message to the user
                reply = QMessageBox.question(
                    self,
                    "Confirm Wallpaper Change",
                    f"Do you want to set the wallpaper from this URI?\n\n{wallpaper_url}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                # store the user's decision for later inspection or logging
                confirmed = reply == QMessageBox.StandardButton.Yes
                self.last_uri_command = {
                    "action": action,
                    "url": wallpaper_url,
                    "confirmed": confirmed
                }
                logging.info(f"URI command confirmation stored: {self.last_uri_command}")

                # act on the user's choice
                if confirmed:
                    # proceed to apply the wallpaper (reuse existing input handling)
                    try:
                        self.ui.urlInput.setText(wallpaper_url)
                        self._set_status("Applying wallpaper from URI...")
                        self._apply_input_string(wallpaper_url)
                    except Exception as e:
                        logging.error(f"Failed to apply wallpaper from URI: {e}", exc_info=True)
                        QMessageBox.critical(self, "Error", f"Failed to apply wallpaper: {e}")
                else:
                    self._set_status("Wallpaper change from URI was cancelled by user")
            else:
                logging.error("setwallpaper action received, but 'url' parameter is missing.")
                QMessageBox.warning(self, "URI Error", "The 'setwallpaper' command is missing the required URL parameter.")
        
        elif action == "openfavorites":
            logging.info("Executing openfavorites command.")
            try:
                folder = get_folder_for_source("favorites")
                if not folder.exists():
                    logging.warning(f"Favorites folder does not exist: {folder}")
                    QMessageBox.warning(self, "Folder Not Found", f"The favorites folder does not exist:\n{folder}")
                else:
                    success = open_folder_in_explorer(folder)
                    if success:
                        self._set_status("Opened Favorites folder")
                        QMessageBox.information(self, "Opened Favorites", f"Opened favorites folder:\n{folder}")
                    else:
                        logging.error(f"Failed to open favorites folder in explorer: {folder}")
                        QMessageBox.warning(self, "Open Failed", f"Could not open folder in file explorer:\n{folder}")
            except Exception as e:
                logging.error(f"Failed to open favorites folder: {e}", exc_info=True)
                QMessageBox.critical(self, "Error", f"Failed to open favorites folder: {e}")
            
        else:
            logging.warning(f"Unknown URI action received: {action}")
            QMessageBox.warning(self, "URI Error", f"Unknown command: '{action}'.")


class DirectDownloadThread(QThread):
    progress = Signal(float, str)   # percent, status message
    done = Signal(str)              # path to downloaded file
    error = Signal(str)

    def __init__(self, url: str, file_path: str, parent=None):
        logging.info(f"Initializing DirectDownloadThread for URL: {url}")
        super().__init__(parent)
        self.url = url
        self.file_path = file_path
        self._cancelled = False

    def run(self):
        try:
            import requests
            logging.info(f"Starting direct download: {self.url} -> {self.file_path}")
            
            self.progress.emit(0, "Connecting...")
            
            # Stream download with progress
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            self.progress.emit(0, f"Downloading... (0%)")
            
            with open(self.file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._cancelled:
                        logging.info("Download cancelled by user")
                        if os.path.exists(self.file_path):
                            os.remove(self.file_path)
                        return
                    
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if total_size > 0:
                            percent = (downloaded_size / total_size) * 100
                            mb_downloaded = downloaded_size / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            
                            status = f"Downloading... {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)"
                            self.progress.emit(percent, status)
                        else:
                            status = f"Downloading... {downloaded_size / (1024 * 1024):.1f} MB"
                            self.progress.emit(0, status)
            
            # Verify download
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                self.progress.emit(100, "Download completed!")
                logging.info(f"Direct download completed successfully: {self.file_path}")
                self.done.emit(self.file_path)
            else:
                error_msg = "Downloaded file is empty or missing"
                logging.error(error_msg)
                self.error.emit(error_msg)
                
        except Exception as e:
            error_msg = f"Direct download failed: {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            # Clean up partial download
            if os.path.exists(self.file_path):
                try:
                    os.remove(self.file_path)
                except:
                    pass
                    
            self.error.emit(error_msg)

    def cancel(self):
        """Cancel the download"""
        self._cancelled = True
        logging.info("Download cancellation requested")

