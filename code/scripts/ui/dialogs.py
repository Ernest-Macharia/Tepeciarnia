from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt


class DownloadProgressDialog(QDialog):
    def __init__(self, parent=None):
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

    def update_progress(self, percent: float, status_msg: str = ""):
        percent_int = int(percent)
        self.progress.setValue(percent_int)
        self.percentage_label.setText(f"{percent_int}%")
        
        if status_msg:
            if "Downloading..." in status_msg:
                details = status_msg.replace("Downloading... ", "")
                self.details_label.setText(details)
            else:
                self.details_label.setText(status_msg)