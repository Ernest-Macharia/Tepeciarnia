import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

from utils.system_utils import which, set_static_desktop_wallpaper
from utils.path_utils import get_weepe_path, get_mpv_path, BASE_DIR
from utils.command_handler import run_and_forget_silent


class WallpaperController:
    def __init__(self):
        self.player_procs = []
        self.current_is_video = False

    def stop(self):
        """Stop all wallpaper processes"""
        logging.info("Stopping all wallpaper processes...")
        
        if sys.platform.startswith("linux"):
            subprocess.call("pkill -f xwinwrap", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("pkill -f mpv", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            # Use taskkill to stop wallpaper processes on Windows
            subprocess.call("taskkill /F /IM weepe.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM mpv.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM ffplay.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Also terminate any tracked processes
        for p in list(self.player_procs):
            try:
                p.terminate()
            except Exception:
                pass
        self.player_procs = []
        self.current_is_video = False
        logging.info("All wallpaper processes stopped")

    def start_video(self, video_path_or_url: str):
        """Starts a video as wallpaper using platform-specific tools."""
        self.stop()
        self.current_is_video = True
        
        video_path = str(video_path_or_url)
        logging.info(f"Starting video wallpaper: {video_path}")
        
        if sys.platform.startswith("win"):
            self._start_video_windows(video_path)
        elif sys.platform.startswith("linux"):
            self._start_video_linux(video_path)
        else:
            self._start_video_fallback(video_path)

    def _start_video_windows(self, video_path: str):
        """Windows-specific video wallpaper implementation"""
        # Primary method: Use Weepe for proper wallpaper
        weepe_exe = get_weepe_path()
        if weepe_exe and weepe_exe.exists():
            try:
                # Use Weepe with the video path - this should set it as actual wallpaper
                cmd = [str(weepe_exe), video_path]
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logging.info("Video wallpaper started with Weepe")
                    return
            except Exception as e:
                logging.error(f"Weepe failed: {e}")

        # Fallback: MPV with Windows-compatible commands ONLY
        mpv_exe = get_mpv_path()
        if mpv_exe and mpv_exe.exists():
            try:
                # WINDOWS-COMPATIBLE MPV COMMANDS ONLY
                # These are the core commands that work reliably on Windows
                cmd = [
                    str(mpv_exe),
                    video_path,
                    "--loop",                    # Loop the video
                    "--no-audio",                # Disable audio (safe)
                    "--no-osd-bar",              # Hide OSD (safe)
                    "--fullscreen",              # Fullscreen mode (safe)
                    "--no-border",               # No window border (safe)
                    "--ontop",                   # Keep on top (safe)
                    "--no-input-default-bindings", # Disable default key bindings
                    "--input-ipc-server=\\.\\pipe\\mpvsocket"  # IPC for control
                ]
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logging.info("Video started with MPV (Windows-compatible commands)")
                    return
            except Exception as e:
                logging.error(f"MPV fallback failed: {e}")

        # Final fallback: ffplay with basic commands
        ffplay = which("ffplay")
        if ffplay:
            try:
                # Basic ffplay commands that work on Windows
                cmd = [
                    ffplay, 
                    "-autoexit", 
                    "-loop", "0", 
                    "-an",                       # No audio
                    "-fs",                       # Fullscreen
                    "-noborder",                 # No border
                    video_path
                ]
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logging.info("Video started with ffplay fallback")
                    return
            except Exception as e:
                logging.error(f"ffplay fallback failed: {e}")
                
        raise RuntimeError("No suitable video wallpaper player found on Windows.")

    def _start_video_linux(self, video_path: str):
        """Linux-specific video wallpaper implementation"""
        # Try xwinwrap + mpv first (proper wallpaper)
        xwinwrap = which("xwinwrap")
        mpv = which("mpv")
        
        if xwinwrap and mpv:
            try:
                # Linux-specific commands for proper wallpaper
                cmd = f"{xwinwrap} -ov -fs -- {mpv} --loop --no-audio --no-osd-bar --wid=WID '{video_path}'"
                p = subprocess.Popen(cmd, shell=True, executable="/bin/bash",
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logging.info("Video wallpaper started with xwinwrap + mpv")
                return
            except Exception as e:
                logging.error(f"xwinwrap failed: {e}")

        # Fallback: mpv fullscreen (Linux-compatible commands)
        if mpv:
            try:
                # Linux-compatible MPV commands
                cmd = [
                    mpv, 
                    "--loop", 
                    "--no-audio", 
                    "--no-osd-bar", 
                    "--fullscreen", 
                    "--no-border",
                    video_path
                ]
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logging.info("Video started with MPV fullscreen")
                return
            except Exception as e:
                logging.error(f"MPV fullscreen failed: {e}")
                
        raise RuntimeError("No suitable video wallpaper player found on Linux.")

    def _start_video_fallback(self, video_path: str):
        """Fallback for other platforms"""
        mpv = which("mpv")
        if mpv:
            try:
                # Universal fallback commands
                cmd = [
                    mpv, 
                    "--loop", 
                    "--no-audio", 
                    "--fullscreen", 
                    "--no-border", 
                    video_path
                ]
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logging.info("Video started with MPV fallback")
                return
            except Exception as e:
                logging.error(f"MPV fallback failed: {e}")
        
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def start_image(self, image_path: str):
        """Set static wallpaper"""
        self.stop()
        self.current_is_video = False
        logging.info(f"Setting static wallpaper: {image_path}")
        try:
            set_static_desktop_wallpaper(image_path)
            logging.info("Static wallpaper set successfully")
        except Exception as e:
            logging.error(f"Failed to set static wallpaper: {e}")
            raise