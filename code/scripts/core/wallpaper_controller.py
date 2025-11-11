import sys
import subprocess
import logging
from pathlib import Path
from typing import Optional

from utils.system_utils import which, set_static_desktop_wallpaper
from utils.path_utils import get_weepe_path, get_mpv_path, BASE_DIR
from utils.command_handler import run_and_forget_silent

# Get logger for this module
logger = logging.getLogger(__name__)


class WallpaperController:
    def __init__(self):
        logger.debug("Initializing WallpaperController")
        self.player_procs = []
        self.current_is_video = False
        self.current_wallpaper_path = None
        logger.info("WallpaperController initialized successfully")

    def stop(self):
        """Stop all wallpaper processes"""
        logger.info("Stopping all wallpaper processes...")
        logger.debug(f"Current state - is_video: {self.current_is_video}, path: {self.current_wallpaper_path}")
        
        if sys.platform.startswith("linux"):
            logger.debug("Stopping Linux wallpaper processes")
            subprocess.call("pkill -f xwinwrap", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("pkill -f mpv", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.debug("Linux process cleanup commands executed")
        elif sys.platform.startswith("win"):
            logger.debug("Stopping Windows wallpaper processes")
            # Use taskkill to stop wallpaper processes on Windows
            subprocess.call("taskkill /F /IM weepe.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM mpv.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("taskkill /F /IM ffplay.exe", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.debug("Windows process cleanup commands executed")
        else:
            logger.warning(f"Unsupported platform for process cleanup: {sys.platform}")
        
        # Also terminate any tracked processes
        logger.debug(f"Terminating {len(self.player_procs)} tracked processes")
        terminated_count = 0
        for p in list(self.player_procs):
            try:
                p.terminate()
                terminated_count += 1
                logger.debug(f"Terminated process: {p.pid}")
            except Exception as e:
                logger.warning(f"Failed to terminate process {p.pid}: {e}")
        
        self.player_procs = []
        self.current_is_video = False
        logger.info(f"Wallpaper processes stopped - {terminated_count} processes terminated")

    def start_video(self, video_path_or_url: str):
        """Starts a video as wallpaper using platform-specific tools."""
        logger.info(f"Starting video wallpaper: {video_path_or_url}")
        self.current_is_video = True
        self.current_wallpaper_path = video_path_or_url
        
        video_path = str(video_path_or_url)
        
        if sys.platform.startswith("win"):
            logger.debug("Using Windows video wallpaper implementation")
            self._start_video_windows(video_path)
        elif sys.platform.startswith("linux"):
            logger.debug("Using Linux video wallpaper implementation")
            self._start_video_linux(video_path)
        else:
            logger.warning(f"Unsupported platform, using fallback: {sys.platform}")
            self._start_video_fallback(video_path)
        
        logger.info(f"Video wallpaper started successfully: {video_path}")

    def _start_video_windows(self, video_path: str):
        """Windows-specific video wallpaper implementation"""
        logger.debug(f"Starting Windows video wallpaper: {video_path}")
        
        # Primary method: Use Weepe for proper wallpaper
        weepe_exe = get_weepe_path()
        logger.debug(f"Weepe executable path: {weepe_exe}")
        
        if weepe_exe and weepe_exe.exists():
            try:
                logger.info("Attempting to start video with Weepe")
                # Use Weepe with the video path - this should set it as actual wallpaper
                cmd = [str(weepe_exe), video_path]
                logger.debug(f"Weepe command: {' '.join(cmd)}")
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logger.info(f"Video wallpaper started with Weepe (PID: {p.pid})")
                    return
                else:
                    logger.warning("Weepe process started but returned None")
            except Exception as e:
                logger.error(f"Weepe failed: {e}", exc_info=True)

        # Fallback: MPV with Windows-compatible commands ONLY
        mpv_exe = get_mpv_path()
        logger.debug(f"MPV executable path: {mpv_exe}")
        
        if mpv_exe and mpv_exe.exists():
            try:
                logger.info("Attempting to start video with MPV fallback")
                # WINDOWS-COMPATIBLE MPV COMMANDS ONLY
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
                logger.debug(f"MPV command: {' '.join(cmd)}")
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logger.info(f"Video started with MPV (PID: {p.pid})")
                    return
                else:
                    logger.warning("MPV process started but returned None")
            except Exception as e:
                logger.error(f"MPV fallback failed: {e}", exc_info=True)

        # Final fallback: ffplay with basic commands
        ffplay = which("ffplay")
        logger.debug(f"FFplay found: {ffplay}")
        
        if ffplay:
            try:
                logger.info("Attempting to start video with ffplay final fallback")
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
                logger.debug(f"FFplay command: {' '.join(cmd)}")
                p = run_and_forget_silent(cmd)
                if p:
                    self.player_procs.append(p)
                    logger.info(f"Video started with ffplay fallback (PID: {p.pid})")
                    return
                else:
                    logger.warning("FFplay process started but returned None")
            except Exception as e:
                logger.error(f"ffplay fallback failed: {e}", exc_info=True)
        
        error_msg = "No suitable video wallpaper player found on Windows."
        logger.error(error_msg)
        logger.error(f"Available players - Weepe: {weepe_exe and weepe_exe.exists()}, MPV: {mpv_exe and mpv_exe.exists()}, FFplay: {bool(ffplay)}")
        raise RuntimeError(error_msg)

    def _start_video_linux(self, video_path: str):
        """Linux-specific video wallpaper implementation"""
        logger.debug(f"Starting Linux video wallpaper: {video_path}")
        
        # Try xwinwrap + mpv first (proper wallpaper)
        xwinwrap = which("xwinwrap")
        mpv = which("mpv")
        logger.debug(f"Linux tools - xwinwrap: {xwinwrap}, mpv: {mpv}")
        
        if xwinwrap and mpv:
            try:
                logger.info("Attempting to start video with xwinwrap + mpv")
                # Linux-specific commands for proper wallpaper
                cmd = f"{xwinwrap} -ov -fs -- {mpv} --loop --no-audio --no-osd-bar --wid=WID '{video_path}'"
                logger.debug(f"xwinwrap command: {cmd}")
                p = subprocess.Popen(cmd, shell=True, executable="/bin/bash",
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logger.info(f"Video wallpaper started with xwinwrap + mpv (PID: {p.pid})")
                return
            except Exception as e:
                logger.error(f"xwinwrap failed: {e}", exc_info=True)

        # Fallback: mpv fullscreen (Linux-compatible commands)
        if mpv:
            try:
                logger.info("Attempting to start video with MPV fullscreen fallback")
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
                logger.debug(f"MPV fallback command: {' '.join(cmd)}")
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logger.info(f"Video started with MPV fullscreen (PID: {p.pid})")
                return
            except Exception as e:
                logger.error(f"MPV fullscreen failed: {e}", exc_info=True)
        
        error_msg = "No suitable video wallpaper player found on Linux."
        logger.error(error_msg)
        logger.error(f"Available players - xwinwrap: {bool(xwinwrap)}, mpv: {bool(mpv)}")
        raise RuntimeError(error_msg)

    def _start_video_fallback(self, video_path: str):
        """Fallback for other platforms"""
        logger.debug(f"Starting fallback video wallpaper for platform: {sys.platform}")
        
        mpv = which("mpv")
        logger.debug(f"Fallback MPV found: {mpv}")
        
        if mpv:
            try:
                logger.info("Attempting to start video with universal MPV fallback")
                # Universal fallback commands
                cmd = [
                    mpv, 
                    "--loop", 
                    "--no-audio", 
                    "--fullscreen", 
                    "--no-border", 
                    video_path
                ]
                logger.debug(f"Universal MPV command: {' '.join(cmd)}")
                p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.player_procs.append(p)
                logger.info(f"Video started with MPV fallback (PID: {p.pid})")
                return
            except Exception as e:
                logger.error(f"MPV fallback failed: {e}", exc_info=True)
        
        error_msg = f"Unsupported platform: {sys.platform}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def start_image(self, image_path: str):
        """Set static wallpaper with proper error handling"""
        logger.info(f"Setting static wallpaper: {image_path}")
        self.current_is_video = False
        self.current_wallpaper_path = image_path
        
        try:
            logger.debug("Calling set_static_desktop_wallpaper")
            set_static_desktop_wallpaper(image_path)
            logger.info("Static wallpaper set successfully")
        except Exception as e:
            logger.error(f"Failed to set static wallpaper: {e}", exc_info=True)
            raise RuntimeError(f"Failed to set static wallpaper: {e}") from e