import sys
import os
import logging
from PySide6.QtWidgets import QApplication

# Set up logger
logger = logging.getLogger(__name__)

# If you want, you can keep this to make sure 'code' package is found
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from code.scripts.utils.path_utils import get_app_root, get_style_path
    # Absolute imports based on 'code' as top-level package
    from code.scripts.setLogging import InitLogging
    from code.scripts.utils.pathResolver import *
    # from code.scripts.ui import icons_rc
    from code.scripts.ui.main_window import MP4WallApp
    logger.debug("Successfully imported modules using 'code' package structure")

except ImportError as e:
    logger.debug(f"Failed to import using 'code' package structure, trying relative imports: {e}")
    from utils.path_utils import get_app_root, get_style_path
    from setLogging import InitLogging
    from utils.pathResolver import *
    from ui import icons_resource_rc
    from ui.main_window import MP4WallApp
    logger.debug("Successfully imported modules using relative imports")

def load_stylesheet(app_instance, filepath):
    """Load a QSS/CSS file and apply it as a stylesheet to the QApplication."""
    try:
        logger.debug(f"Loading stylesheet from: {filepath}")
        with open(filepath, "r") as f:
            stylesheet = f.read()
            app_instance.setStyleSheet(stylesheet)
        logger.info("Stylesheet loaded successfully")
    except FileNotFoundError:
        logger.error(f"Stylesheet file not found at {filepath}")
    except Exception as e:
        logger.error(f"Failed to load stylesheet: {e}")


def main():
    logger.info("Starting MP4Wall application")
    
    # Initialize logging
    logger.debug("Initializing logging system")
    InitLogging()

    # Create the Qt application
    logger.debug("Creating QApplication instance")
    app = QApplication(sys.argv)

    # Load stylesheet
    stylesheet_path = get_style_path(get_app_root())
    logger.debug(f"Resolved stylesheet path: {stylesheet_path}")
    load_stylesheet(app, stylesheet_path)

    # Create and show main window
    logger.debug("Creating main window")
    window = MP4WallApp()
    logger.debug("Showing main window")
    window.show()

    # Run the Qt event loop
    logger.info("Starting Qt event loop")
    try:
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Qt event loop failed: {e}")
        raise


if __name__ == "__main__":
    main()