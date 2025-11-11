import time
import random
import logging
from pathlib import Path
from threading import Thread, Event
from typing import Optional, Callable

from utils.path_utils import COLLECTION_DIR, VIDEOS_DIR, IMAGES_DIR, FAVS_DIR


class WallpaperScheduler:
    def __init__(self):
        self.interval_minutes = 30
        self.source = str(COLLECTION_DIR)
        self.range_type = "all"
        self.is_running = False
        self.thread = None
        self.stop_event = Event()
        self.change_callback: Optional[Callable] = None
        self.last_wallpaper = None

    def set_change_callback(self, callback: Callable):
        """Set callback for when wallpaper should change"""
        self.change_callback = callback

    def set_range(self, range_type: str):
        """Set range type: all, wallpaper, or mp4"""
        self.range_type = range_type

    def start(self, source: str, interval_minutes: int):
        """Start the scheduler"""
        if self.is_running:
            self.stop()
        
        self.source = source
        self.interval_minutes = interval_minutes
        self.is_running = True
        self.stop_event.clear()
        
        self.thread = Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        logging.info(f"Scheduler started: {source}, interval: {interval_minutes}min")

    def stop(self):
        """Stop the scheduler"""
        self.is_running = False
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        logging.info("Scheduler stopped")

    def is_active(self):
        """Check if scheduler is running"""
        return self.is_running

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running and not self.stop_event.is_set():
            try:
                # Wait for the interval
                self.stop_event.wait(self.interval_minutes * 60)
                
                if self.stop_event.is_set():
                    break
                
                if self.is_running and self.change_callback:
                    # Get a random wallpaper that's different from the current one
                    wallpaper = self._get_random_wallpaper()
                    if wallpaper and wallpaper != self.last_wallpaper:
                        self.last_wallpaper = wallpaper
                        self.change_callback(wallpaper)
                    elif wallpaper:
                        logging.info("Skipping same wallpaper selection")
                        
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def _get_random_wallpaper(self):
        """Get a random wallpaper file"""
        files = self._get_media_files()
        if files:
            return random.choice(files)
        return None

    def _get_media_files(self):
        """Get media files based on current range"""
        files = []
        
        # Define search folders based on source
        if self.source == str(FAVS_DIR):
            search_folders = [FAVS_DIR]
        elif self.source == str(COLLECTION_DIR):
            search_folders = [VIDEOS_DIR, IMAGES_DIR, FAVS_DIR]
        else:
            search_folders = [Path(self.source)]
        
        # Define extensions based on range type
        if self.range_type == "mp4":
            extensions = ('.mp4', '.mkv', '.webm', '.avi', '.mov')
        elif self.range_type == "wallpaper":
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        else:  # "all"
            extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.mp4', '.mkv', '.webm', '.avi', '.mov')
        
        for folder in search_folders:
            if folder.exists():
                folder_files = [
                    f for f in folder.iterdir() 
                    if f.is_file() and f.suffix.lower() in extensions
                ]
                files.extend(folder_files)
        
        return files