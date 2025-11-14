from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QApplication
from PySide6.QtCore import Qt, QTimer
import logging


class DownloadProgressDialog(QDialog):
    def __init__(self, parent=None):
        logging.debug("Initializing DownloadProgressDialog")
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
        
        self.percentage_label = QLabel("0%", self)
        self.percentage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.percentage_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.details_label = QLabel("Starting download...", self)
        self.details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details_label.setStyleSheet("font-size: 11px; color: #666;")
        
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        layout.addWidget(self.percentage_label)
        layout.addWidget(self.details_label)
        
        logging.info("DownloadProgressDialog initialized successfully")

    def update_progress(self, percent: float, status_msg: str = ""):
        """Update download progress with logging"""
        percent_int = int(percent)
        logging.debug(f"Updating progress: {percent_int}% - {status_msg}")
        
        # Update progress bar
        self.progress.setValue(percent_int)
        self.percentage_label.setText(f"{percent_int}%")
        
        if status_msg:
            if "Downloading..." in status_msg:
                details = status_msg.replace("Downloading... ", "")
                self.details_label.setText(details)
                logging.debug(f"Download progress details: {details}")
            else:
                self.details_label.setText(status_msg)
                logging.debug(f"Download status: {status_msg}")
        
        # Log significant progress milestones
        if percent_int in [0, 25, 50, 75, 90, 100]:
            logging.info(f"Download progress milestone: {percent_int}% - {status_msg}")
        
        # Log when download is complete
        if percent_int == 100:
            logging.info("Download progress reached 100% - download complete")

    def show(self):
        """Override show method to log when dialog is displayed"""
        logging.info("Showing DownloadProgressDialog")
        super().show()

    def close(self):
        """Override close method to log when dialog is closed"""
        logging.info("Closing DownloadProgressDialog")
        super().close()

    def reject(self):
        """Handle dialog cancellation with logging"""
        logging.warning("DownloadProgressDialog cancelled by user")
        super().reject()

    def accept(self):
        """Handle dialog acceptance with logging"""
        logging.info("DownloadProgressDialog accepted")
        super().accept()

class ShutdownProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.shutdown_steps = [
            ("Stopping wallpaper processes...", 25),
            ("Stopping scheduler...", 50), 
            ("Cleaning up resources...", 75),
            ("Saving settings...", 90),
            ("Shutdown complete!", 100)
        ]
        self.current_step = 0
        
    def setup_ui(self):
        self.setWindowTitle("Shutting Down Tapeciarnia...")
        self.setFixedSize(400, 150)
        self.setModal(True)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Shutting Down Tapeciarnia")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing shutdown...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Progress percentage label
        self.percentage_label = QLabel("0%")
        self.percentage_label.setAlignment(Qt.AlignCenter)
        self.percentage_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4CAF50;")
        layout.addWidget(self.percentage_label)
    
    def update_progress(self, value: int, status: str = ""):
        """Update progress bar and status with detailed logging"""
        logging.info(f"Shutdown progress: {value}% - {status}")
        
        self.progress_bar.setValue(value)
        self.percentage_label.setText(f"{value}%")
        
        if status:
            self.status_label.setText(status)
        
        # Force UI update
        QApplication.processEvents()
    
    def execute_shutdown_sequence(self):
        """Execute the shutdown sequence with progress updates"""
        logging.info("Starting shutdown sequence")
        
        for step_text, step_progress in self.shutdown_steps:
            self.update_progress(step_progress, step_text)
            
            # Simulate some work being done
            QTimer.singleShot(500, lambda: None)
            QApplication.processEvents()
            
            # Actual shutdown operations are handled by the main app
            # This just shows the visual progress
        
        # Final delay before closing
        QTimer.singleShot(1000, self.accept)
    
    def showEvent(self, event):
        """Start the shutdown sequence when dialog is shown"""
        super().showEvent(event)
        QTimer.singleShot(100, self.execute_shutdown_sequence)
    
    def closeEvent(self, event):
        """Prevent closing during shutdown sequence"""
        if self.progress_bar.value() < 100:
            event.ignore()
        else:
            super().closeEvent(event)