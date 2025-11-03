from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property


class FadeOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self._pixmap_old = None
        self._pixmap_new = None
        self._opacity = 0.0
        self._anim = None
        if parent:
            self.resize(parent.size())
        else:
            self.resize(800, 600)

    def set_pixmaps(self, old, new):
        self._pixmap_old = old
        self._pixmap_new = new
        self._opacity = 0.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._pixmap_old:
            painter.setOpacity(1.0)
            painter.drawPixmap(self.rect(), self._pixmap_old)
        if self._pixmap_new:
            painter.setOpacity(self._opacity)
            painter.drawPixmap(self.rect(), self._pixmap_new)

    def animate_to(self, duration=600):
        anim = QPropertyAnimation(self, b"overlayOpacity", self)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        anim.start()
        self._anim = anim

    def getOpacity(self):
        return self._opacity

    def setOpacity(self, v):
        self._opacity = float(v)
        self.update()

    overlayOpacity = Property(float, getOpacity, setOpacity)


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
        
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()