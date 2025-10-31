import sys
import os
import platform
import subprocess
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QPushButton, QLineEdit, QCheckBox, 
    QComboBox, QHBoxLayout, QVBoxLayout, QSystemTrayIcon, QMenu, QAction, 
    QFileDialog, QMessageBox
)
# Added QEvent for state change detection
from PyQt5.QtCore import Qt, QCoreApplication, QTimer, QEvent 

# --- HELPER FUNCTIONS COPIED FROM run_mpv_silent.py ---
# These are necessary for silent background execution on Windows.
CREATE_NO_WINDOW = 0x08000000

def run_and_forget_silent(command_parts, cwd=None):
    """
    Executes a command on Windows silently and immediately returns 
    without waiting for the command to finish. (AutoIt 'Run' Equivalent).
    """
    if platform.system() != "Windows":
        # Non-Windows systems don't have CREATE_NO_WINDOW, run normally
        return subprocess.Popen(command_parts, cwd=cwd, start_new_session=True)

    try:
        # Use CREATE_NO_WINDOW to suppress the console flicker
        process = subprocess.Popen(
            command_parts,
            creationflags=CREATE_NO_WINDOW,
            cwd=cwd
        )
        print(f"Successfully launched PID: {process.pid} in the background.")
        return process
    except FileNotFoundError:
        print(f"Error: Executable not found. Command: {command_parts[0]}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during silent run: {e}")
        return None
# --- END HELPER FUNCTIONS ---


# --- CONFIGURATION SIMULATION ---
# In a real app, this would read from a config.ini file.
def read_ini_key(key):
    """Simulates reading configuration keys from the config.ini file."""
    # Hardcoded values based on AutoIt defaults for demonstration
    config = {
        "redResetButton": False,
        "multiScreenDefault": False,
        "askMultiScreen": False,
        "autoPauseFeature": False,
        "forceAutorefresh": False,
    }
    # Return bool or default to False if not found
    return config.get(key, False)


class MP4WallApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MP4 Wall")
        self.setGeometry(183, 124, 513, 75)
        self.setFixedSize(513, 75) # Fixed size like the original GUI

        self.working_dir = os.path.dirname(os.path.abspath(__file__))
        self.multi_screen = read_ini_key("multiScreenDefault")
        self.tray_icon = None

        self._setup_ui()
        self._setup_tray_icon()
        self._init_gui_state()
        
    def changeEvent(self, event):
        """
        Overrides changeEvent to treat minimization as hiding the window to the tray.
        When the user clicks the minimize button, it triggers self.hide() instead.
        """
        if event.type() == QEvent.WindowStateChange:
            # Check if the window is being minimized
            if self.isMinimized():
                # Hide the window instead of minimizing it to the taskbar
                self.hide()
                
        super().changeEvent(event)


    def _setup_ui(self):
        # Central Widget and Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. Top Row (Input and Apply Button)
        top_row = QHBoxLayout()
        self.inputPath = QLineEdit()
        self.inputPath.setPlaceholderText("Browse and select video")
        self.applyb = QPushButton("Apply")
        self.applyb.clicked.connect(self.handle_apply)

        top_row.addWidget(self.inputPath)
        top_row.addWidget(self.applyb)

        # 2. Bottom Row (Controls)
        bottom_row = QHBoxLayout()
        
        self.winStart = QCheckBox("Set on windows startup")
        self.winStart.stateChanged.connect(self.on_win_start)
        
        self.comboScreens = QComboBox()
        self.comboScreens.currentIndexChanged.connect(self.handle_combo_change)
        
        self.browseb = QPushButton("Browse")
        self.browseb.clicked.connect(self.browse_files)
        
        self.hideb = QPushButton("Hide")
        self.hideb.clicked.connect(self.hide_window)
        
        self.resetb = QPushButton("Reset")
        self.resetb.clicked.connect(self.handle_reset)
        
        # Assemble bottom row controls (mimicking AutoIt placement)
        bottom_row.addWidget(self.winStart)
        bottom_row.addSpacing(70) # Spacing to push elements right
        bottom_row.addWidget(self.comboScreens)
        bottom_row.addWidget(self.browseb)
        bottom_row.addWidget(self.hideb)
        bottom_row.addWidget(self.resetb)

        main_layout.addLayout(top_row)
        main_layout.addLayout(bottom_row)

    def _setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(
            QApplication.style().StandardPixmap.SP_DriveDVDIcon) # Placeholder icon
        )
        self.tray_icon.setToolTip("MP4 Wall")
        
        tray_menu = QMenu()
        
        action_show = QAction("Show", self)
        action_show.triggered.connect(self.show_window)
        tray_menu.addAction(action_show)

        action_hide = QAction("Hide", self)
        action_hide.triggered.connect(self.hide_window)
        tray_menu.addAction(action_hide)

        tray_menu.addSeparator()
        
        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        tray_menu.addAction(action_exit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._handle_tray_activation)
        self.tray_icon.show()

    def _handle_tray_activation(self, reason):
        # Mimics TRAY_DBLCLICK_PRIMARY
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()

    def _init_gui_state(self):
        # Simulating Multi-Screen Logic
        monitor_count = QApplication.desktop().screenCount()
        
        if self.multi_screen and monitor_count > 1:
            self.applyb.setDisabled(True)
            self.browseb.setDisabled(True)
            self.comboScreens.clear()
            for i in range(monitor_count):
                self.comboScreens.addItem(f"Apply on screen {i + 1}")
        else:
            self.comboScreens.setVisible(False)

    # --- GUI Event Handlers ---

    def handle_apply(self):
        self.applyb.setDisabled(True)
        self.set_wallpaper()
        self.applyb.setEnabled(True)
        self.winStart.setEnabled(True)

    def handle_reset(self):
        self.reset_wallpaper()
        self.winStart.setChecked(False)
        self.winStart.setDisabled(True)

    def browse_files(self):
        # Simulates FileOpenDialog
        file_filter = "Videos (*.avi *.mp4 *.gif *.mkv *.webm);;All Files (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select the video for wallpaper", 
            os.getcwd(), # Start browsing in current directory
            file_filter
        )
        if file_path:
            self.inputPath.setText(file_path)
            self.winStart.setEnabled(True)
            self.winStart.setChecked(False) # AutoIt sets UNCHECKED after successful browse
        else:
            print("File selection cancelled.")

    def handle_combo_change(self):
        # Logic run when combo box changes (resets winStart and input)
        self.applyb.setEnabled(True)
        self.browseb.setEnabled(True)
        self.winStart.setChecked(False)
        self.winStart.setDisabled(True)
        self.inputPath.setText("")

    def hide_window(self):
        self.hide()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    # --- System & Wallpaper Logic ---

    def reset_wallpaper(self):
        self.kill_all()
        self.applyb.setEnabled(True)
        self.inputPath.setText("")
        # Add logic here to reset desktop background to an image if needed
        QMessageBox.information(self, "Reset", "All wallpaper processes killed.")


    def on_win_start(self, state):
        # NOTE: Shortcut creation/deletion requires win32com.client on Windows
        # We will SIMPLY print the action for portability and security.
        startup_path = os.path.join(
            os.environ.get("APPDATA", os.path.expanduser("~")), 
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup"
        )
        
        app_name = "Mp4Wall.exe" # Assuming the compiled executable name
        video_path = self.inputPath.text()

        if state == Qt.Checked:
            print(f"ACTION: Creating Windows Startup Shortcut for {app_name} with args: '{video_path}'")
            # If using pywin32: FileCreateShortcut equivalent logic would go here
        else:
            print(f"ACTION: Deleting Windows Startup Shortcut for {app_name}")
            # If using pywin32: FileDelete equivalent logic would go here

    
    def set_wallpaper(self):
        input_path = self.inputPath.text()
        
        if not input_path:
            QMessageBox.warning(self, "Warning", "Please select a video file first.")
            return

        # Simulating DownloadVideoIfURL and forceWebview checks
        is_url = input_path.lower().startswith("http")
        force_webview = read_ini_key("forceWebview")
        
        # If it's a file path and NOT forceWebview, proceed with MPV/wp.exe logic
        if not is_url and not force_webview:
            self.kill_all() # Ensure previous instances are gone

            # Path to external tools (assuming relative structure from AutoIt)
            bin_path = os.path.join(self.working_dir, "bin")
            wp_exe_path = os.path.join(bin_path, "weebp", "wp.exe")
            
            if not os.path.exists(wp_exe_path):
                QMessageBox.critical(self, "Error", f"Could not find wp.exe at: {wp_exe_path}")
                return

            # 1. Run MPV command (runs video player)
            mpv_run_command = [
                wp_exe_path,
                "run", "mpv", 
                # Quote the path to handle spaces
                input_path, 
                "--input-ipc-server=\\.\pipe\mpvsocket"
            ]
            run_and_forget_silent(mpv_run_command, cwd=os.path.join(bin_path, "mpv"))
            print(f"Launched MPV command: {mpv_run_command}")

            # 2. Add as wallpaper command (attaches video player to desktop)
            add_command = [
                wp_exe_path, 
                "add", "--wait", "--fullscreen", "--class", "mpv"
            ]
            run_and_forget_silent(add_command, cwd=os.path.join(bin_path, "weebp"))
            print(f"Launched WP add command: {add_command}")

            # 3. Optional: AutoPause and Refresh Logic
            if platform.system() == "Windows":
                 QTimer.singleShot(2000, lambda: self._run_optional_tools())

        elif is_url or force_webview:
            QMessageBox.information(self, "Web View", "Web view logic would run here (e.g., using litewebview.exe).")
            # Kill existing processes first
            self.kill_all()


    def _run_optional_tools(self):
        # Runs tools that depend on the wallpaper being started (e.g., refresh, autopause)
        bin_path = os.path.join(self.working_dir, "bin", "tools")
        
        # Simulating refresh.exe
        if read_ini_key("forceAutorefresh"):
            refresh_path = os.path.join(bin_path, "refresh.exe")
            # Note: GetViewId logic is complex and skipped; we pass a dummy argument '0x0'
            run_and_forget_silent([refresh_path, "0x0"])
            print("Launched refresh.exe")

        # Simulating autoPause.exe
        if read_ini_key("autoPauseFeature"):
            auto_pause_path = os.path.join(bin_path, "autoPause.exe")
            run_and_forget_silent([auto_pause_path])
            print("Launched autoPause.exe")


    def kill_all(self):
        # Uses Windows 'taskkill' command for robust process termination
        # This replaces the AutoIt ProcessClose loop.
        processes_to_kill = ['mpv.exe', 'wp.exe', 'litewebview.exe', 'Win32WebViewHost.exe', 'autopause.exe', 'mousesender.exe']
        
        if platform.system() == "Windows":
            print("Attempting to kill background processes...")
            # /F (force kill) /IM (image name)
            command = ["taskkill", "/F", "/IM", "", "/T"]
            for proc in processes_to_kill:
                command[3] = proc # Set the image name dynamically
                try:
                    subprocess.run(command, check=False, creationflags=CREATE_NO_WINDOW, capture_output=True)
                    print(f"Killed: {proc}")
                except Exception as e:
                    # Usually, if a process doesn't exist, this fails silently
                    print(f"Process kill failed for {proc}: {e}")
        else:
            print("Non-Windows system: Skipping taskkill.")


    def closeEvent(self, event):
        # On close (X button), hide the window instead of exiting, similar to tray behavior
        self.hide()
        event.ignore()

    def close(self):
        # Only exit the application when explicitly told to by the tray menu
        self.tray_icon.hide()
        QCoreApplication.quit()


if __name__ == "__main__":
    # Ensure only one instance runs (common for tray apps)
    # QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling) # Optional Dpi fix
    
    app = QApplication(sys.argv)
    window = MP4WallApp()
    sys.exit(app.exec_())
