import sys
import subprocess
import logging
import platform
import os
from utils.system_utils import which, set_static_desktop_wallpaper
from utils.path_utils import get_weebp_path, get_mpv_path, BASE_DIR,get_bin_path,get_tools_path
import time
from utils.command_handler import run_and_forget_silent,run_blocking_silent_command
import re
import time

from PySide6.QtWidgets import QMessageBox
class WallpaperController:
    def __init__(self):
        self.player_procs = []
        self.current_is_video = False
        self.tools_path = get_tools_path()
        self.weebp_path = get_weebp_path()
        self.mpv_path = get_mpv_path()
        self.refresh_limit = 6
        self.refresh_count = 0
        if not self._check_weebp_and_mpv():
            # show and error window
            QMessageBox.critical(None, "Error", "weebp or mpv executable not found. Video wallpaper functionality may be limited.")
            # exit main app
            sys.exit(1) 
            return

    def _check_weebp_and_mpv(self) -> bool:
        """Check if weebp and mpv executables are available"""
        weebp_exists = self.weebp_path is not None and self.weebp_path.exists()
        mpv_exists = self.mpv_path is not None and self.mpv_path.exists()
        return weebp_exists and mpv_exists

    def _run_auto_pause(self):
        # Runs the autoPause.exe tool to manage pausing based on user activity
        auto_pause_path = os.path.join(self.tools_path, "autoPause.exe")
        run_and_forget_silent([auto_pause_path])
        logging.info("Launched autoPause.exe")
    
    def _run_refresh(self):
        view_id = self.get_view_id().strip()
        if view_id == "0" and self.refresh_count < self.refresh_limit:
            self.refresh_count += 1
            time.sleep(1)
            self._run_refresh()
        else:
            # Runs the refresh.exe tool to refresh the wallpaper
            refresh_path = os.path.join(self.tools_path, "refresh.exe")
            run_and_forget_silent([refresh_path, f"0x{view_id}"])
        logging.info("Launched refresh.exe")

    def run_optional_tools(self):
        self._run_auto_pause()
        self._run_refresh()


    def stop(self):
        """Stop all wallpaper processes"""
        logging.info("Stopping all wallpaper processes...")
        
        if sys.platform.startswith("linux"):
            subprocess.call("pkill -f xwinwrap", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call("pkill -f mpv", shell=True, 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform.startswith("win"):
            if self.current_is_video:
                self.stop_for_windows()
        
        self.current_is_video = False
        logging.info("All wallpaper processes stopped")

    def stop_for_windows(self):
        # clear_playlist
        """Stops wallpaper processes on Windows using taskkill."""
        self._clear_playlist()
        # Uses Windows 'taskkill' command for robust process termination
        # This replaces the AutoIt ProcessClose loop.
        processes_to_kill = ['mpv.exe', 'wp.exe', 'autopause.exe', 'refresh.exe']
        
        if platform.system() == "Windows":
            logging.debug("Attempting to kill background processes...")
            # /F (force kill) /IM (image name)
            command = ["taskkill", "/F", "/IM", "", "/T"]
            for proc in processes_to_kill:
                command[3] = proc # Set the image name dynamically
                try:
                    subprocess.run(command, check=False, creationflags=0x08000000, capture_output=True)
                    logging.debug(f"Killed: {proc}")
                except Exception as e:
                    # Usually, if a process doesn't exist, this fails silently
                    logging.debug(f"Process kill failed for {proc}: {e}")
        else:
            print("Non-Windows system: Skipping taskkill.")

    def start_video(self, video_path_or_url: str):
        
        """Starts a video as wallpaper using platform-specific tools."""
        video_path = str(video_path_or_url)
        logging.debug(f"Is current video: {self.current_is_video}")
        if platform.system() == "Windows":
            if self.current_is_video:
                # perfrom transition if already video is playing
                logging.info("Switching video wallpaper...")
                self._play_next_video(str(video_path_or_url))
                return
            # Start new video wallpaper
            self._start_video_windows(video_path)
            self.current_is_video = True            
            logging.info(f"Starting video wallpaper: {video_path}")

        
        elif sys.platform.startswith("linux"):
            self._start_video_linux(video_path)
        else:
            self._start_video_fallback(video_path)

    def _clear_playlist(self):   
        """Clears the MPV playlist via weebp."""

        command = [
            str(self.weebp_path),
            "mpv",
            "playlist-clear"
        ]

        run_and_forget_silent(command,cwd=self.mpv_path.parents[0])
        time.sleep(1)  # Give MPV time to process the command


    def _play_next_video(self,video_path: str):

        """Plays the next video by stopping current and starting new one."""
        logging.info(f"Switching to next video wallpaper: {video_path}")

        # appand video to the playlist of the existing mpv process
        command = [
            str(self.weebp_path),
            "mpv",
            "loadfile",
            video_path,
            "append"
        ]

        run_and_forget_silent(command,cwd=self.mpv_path.parents[0])
        time.sleep(1)  # Give MPV time to process the new file
        # play the newly added video
        command = [
            str(self.weebp_path),
            "mpv",
            "playlist-next"
        ]
        run_and_forget_silent(command,cwd=self.mpv_path.parents[0])


    def _play_previous_video(self,video_path: str):

        """Plays the previous video by going back."""
        logging.info(f"Switching to previous video wallpaper: {video_path}")

        weebp_exe = get_weebp_path()

        command = [
            str(weebp_exe),
            "mpv",
            "playlist-prev"
        ]
        run_and_forget_silent(command,cwd=self.mpv_path.parents[0])

    def _start_video_windows(self, video_path: str):
        """Windows-specific video wallpaper implementation"""
        # Primary method: Use weebp for proper wallpaper
        try:
            # WINDOWS-COMPATIBLE MPV COMMANDS ONLY
            # These are the core commands that work reliably on Windows
            mpv_run_command = [
                str(self.weebp_path),
                "run", 
                "mpv",
                video_path,
                r"--input-ipc-server=\\.\pipe\mpvsocket"
                ]   
            # 2. Add as wallpaper command (attaches video player to desktop)
            add_command = [
                str(self.weebp_path), 
                "add", "--wait", "--fullscreen", "--class", "mpv"
            ]

            run_mvp = run_and_forget_silent(mpv_run_command,cwd=self.mpv_path.parents[0])
            time.sleep(1)  # Give mvp time to attach
            run_weebp = run_and_forget_silent(add_command,cwd=self.mpv_path.parents[0])
            time.sleep(1)  # Give weebp time to attach

            self.run_optional_tools()
            # self._run_refresh()
            
            if run_mvp and run_weebp:
                self.player_procs.append(run_mvp)
                self.player_procs.append(run_weebp)
                logging.info("Video started with MPV (Windows-compatible commands)")
                return
        except Exception as e:
            logging.error(f"MPV fallback failed: {e}")



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
        if self.current_is_video:
            logging.info(f"Setting static wallpaper: {image_path}")
            try:
                set_static_desktop_wallpaper(image_path)
                logging.info("Static wallpaper set successfully")
            except Exception as e:
                logging.error(f"Failed to set static wallpaper: {e}")
                raise

            self.stop()
            self.current_is_video = False
            return

        try:
            set_static_desktop_wallpaper(image_path)
            logging.info("Static wallpaper set successfully")
        except Exception as e:
            logging.error(f"Failed to set static wallpaper: {e}")
            raise


    # It's only working on Windows with weebp
    # Test it thoroughly before enabling on other platforms
    def get_view_id(self) -> str:
        """
        Run the wp.exe 'ls' command in old_work\\bin\\weebp and return the first view id found.
        Tries to match a line containing 'mpv' . Returns "0" if none found.
        """

        try:
            proc = subprocess.run([self.weebp_path, "ls"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            output = proc.stdout
        except Exception:
            return "0"
        
        logging.info(f"Command wp.exe ls:\n {output}")
        # First try to find 'mpv' line
        pattern = r'\[([0-9A-Fa-f]{8})\].*?mpv'
        m = re.search(pattern, output)
        if m:
            logging.debug(f"Found view id with mpv: {m.group(1)}")
            return m.group(1)
        # Fallback: just get the first view id
        logging.error("Falling back to first view id")
        return "0"