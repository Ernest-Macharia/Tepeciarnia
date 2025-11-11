from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
import logging

# Get logger for this module
logger = logging.getLogger(__name__)


class DownloadProgressDialog(QDialog):
    def __init__(self, parent=None):
        logger.debug("Initializing DownloadProgressDialog")
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
        
        logger.info("DownloadProgressDialog initialized successfully")

    def update_progress(self, percent: float, status_msg: str = ""):
        """Update download progress with logging"""
        percent_int = int(percent)
        logger.debug(f"Updating progress: {percent_int}% - {status_msg}")
        
        # Update progress bar
        self.progress.setValue(percent_int)
        self.percentage_label.setText(f"{percent_int}%")
        
        if status_msg:
            if "Downloading..." in status_msg:
                details = status_msg.replace("Downloading... ", "")
                self.details_label.setText(details)
                logger.debug(f"Download progress details: {details}")
            else:
                self.details_label.setText(status_msg)
                logger.debug(f"Download status: {status_msg}")
        
        # Log significant progress milestones
        if percent_int in [0, 25, 50, 75, 90, 100]:
            logger.info(f"Download progress milestone: {percent_int}% - {status_msg}")
        
        # Log when download is complete
        if percent_int == 100:
            logger.info("Download progress reached 100% - download complete")

    def show(self):
        """Override show method to log when dialog is displayed"""
        logger.info("Showing DownloadProgressDialog")
        super().show()

    def close(self):
        """Override close method to log when dialog is closed"""
        logger.info("Closing DownloadProgressDialog")
        super().close()

    def reject(self):
        """Handle dialog cancellation with logging"""
        logger.warning("DownloadProgressDialog cancelled by user")
        super().reject()

    def accept(self):
        """Handle dialog acceptance with logging"""
        logger.info("DownloadProgressDialog accepted")
        super().accept()