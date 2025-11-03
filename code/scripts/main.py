import sys
import os
from PySide6.QtWidgets import QApplication

sys.path.append(os.path.dirname(__file__))
from .ui.main_window import MP4WallApp


def main():
    app = QApplication(sys.argv)
    window = MP4WallApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()