import sys
import os
from PySide6.QtWidgets import QApplication
from code.scripts.utils.path_utils import get_app_root, get_style_path

# If you want, you can keep this to make sure 'code' package is found
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Absolute imports based on 'code' as top-level package
from code.scripts.setLogging import InitLogging
from code.scripts.utils.pathResolver import *
from code.scripts.ui import icons_rc
from code.scripts.ui.main_window import MP4WallApp


def load_stylesheet(app_instance, filepath):
    """Load a QSS/CSS file and apply it as a stylesheet to the QApplication."""
    try:
        with open(filepath, "r") as f:
            stylesheet = f.read()
            app_instance.setStyleSheet(stylesheet)
            print(f"Successfully loaded stylesheet from: {filepath}")
    except FileNotFoundError:
        print(f"Error: Stylesheet file not found at {filepath}")


def main():
    # Initialize logging
    InitLogging()

    # Create the Qt application
    app = QApplication(sys.argv)

    # Load stylesheet
    load_stylesheet(app, get_style_path(get_app_root()))

    # Create and show main window
    window = MP4WallApp()
    window.show()

    # Run the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
