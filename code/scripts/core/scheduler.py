import random
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer

from utils.path_utils import COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR


class WallpaperScheduler:
    def __init__(self):
        self.timer = QTimer()
        self.source: Optional[str] = None
        self.interval_minutes: int = 30
        self.current_range: str = "all"
        self.change_callback = None

    def set_change_callback(self, callback):
        """Set the callback function to be called when wallpaper should change"""
        self.change_callback = callback
        self.timer.timeout.connect(self._on_tick)

    def start(self, source: str, interval_minutes: int):
        """Start the scheduler"""
        self.source = source
        self.interval_minutes = max(1, interval_minutes)
        self.timer.start(self.interval_minutes * 60 * 1000)

    def stop(self):
        """Stop the scheduler"""
        self.timer.stop()
        self.source = None

    def is_active(self) -> bool:
        return self.timer.isActive()

    def set_range(self, range_type: str):
        """Set the current range (all, wallpaper, mp4)"""
        self.current_range = range_type

    def _on_tick(self):
        """Called when scheduler timer ticks"""
        if not self.source or not self.change_callback:
            return

        src = Path(self.source)
        if src.exists() and src.is_dir():
            files = self._get_media_files()
            if files:
                chosen = str(random.choice(files))
                self.change_callback(chosen)

    def _get_media_files(self):
        """Get media files based on current range selection"""
        files = []
        
        if self.current_range == "mp4":  # Videos only
            search_folders = [VIDEOS_DIR, FAVS_DIR]
            extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        elif self.current_range == "wallpaper":  # Images only  
            search_folders = [IMAGES_DIR, FAVS_DIR]
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        else:  # All media types
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