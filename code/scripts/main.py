import sys
import logging
# Note: Using PySide6 imports as specified in your current code
from PySide6.QtWidgets import QApplication 

# --- DYNAMIC IMPORTS & CONTROLLER SETUP ---
try:
    # If you want, you can keep this to make sure 'code' package is found
    # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    # Absolute imports based on 'code' as top-level package
    from code.scripts.utils.path_utils import get_app_root, get_style_path
    from code.scripts.setLogging import InitLogging
    from code.scripts.utils.pathResolver import *
    from code.scripts.ui import icons_resource_rc
    from code.scripts.ui.main_window import TapeciarniaApp
    
    # URI Imports (Absolute)
    from code.scripts.utils.uri_handler import parse_uri_command 
    from code.scripts.core.wallpaper_controller import WallpaperController # Assumed path
    
    logging.debug("Successfully imported modules using 'code' package structure")

except ImportError as e:
    logging.debug(f"Failed to import using 'code' package structure, trying relative imports: {e}")
    
    # Relative Imports
    from utils.path_utils import get_app_root, get_style_path
    from setLogging import InitLogging
    from utils.pathResolver import *
    from ui import icons_resource_rc
    from ui.main_window import TapeciarniaApp
    
    # URI Imports (Relative)
    from utils.uri_handler import parse_uri_command 
    
    # Controller Placeholder (used if WallpaperController import fails)
    try:
        from core.wallpaper_controller import WallpaperController 
    except ImportError:
        class WallpaperController:
            """Placeholder for the controller to prevent crashes if core is missing."""
            def __init__(self):
                pass
            def handle_uri_command(self, action, params):
                logging.warning(f"CORE NOT FOUND: Received URI command: Action={action}, Params={params}")
                
    logging.debug("Successfully imported modules using relative imports")
# --- END DYNAMIC IMPORTS ---


def load_stylesheet(app_instance, filepath):
    """Load a QSS/CSS file and apply it as a stylesheet to the QApplication."""
    try:
        logging.debug(f"Loading stylesheet from: {filepath}")
        with open(filepath, "r") as f:
            stylesheet = f.read()
            app_instance.setStyleSheet(stylesheet)
        logging.info("Stylesheet loaded successfully")
    except FileNotFoundError:
        logging.error(f"Stylesheet file not found at {filepath}")
    except Exception as e:
        logging.error(f"Failed to load stylesheet: {e}")


def main():
    logging.info("Starting Tapeciarnia application")
    
    # 1. Initialize logging (Needs to be done first)
    logging.debug("Initializing logging system")
    InitLogging()

    # 2. Create the Qt application
    logging.debug("Creating QApplication instance")
    app = QApplication(sys.argv)

    # 3. Check for URI Command
    uri_command = None
    if len(sys.argv) > 1 and sys.argv[1].startswith('tapeciarnia://'):
        uri_command = sys.argv[1]

    # 4. Load stylesheet (Needed regardless of launch mode)
    stylesheet_path = get_style_path(get_app_root())
    logging.debug(f"Resolved stylesheet path: {stylesheet_path}")
    load_stylesheet(app, stylesheet_path)

    # 5. Handle URI Launch (Priority Mode)
    if uri_command:
        logging.info(f"Detected URI launch: {uri_command}")
        action, params = parse_uri_command(uri_command)
        
        if action:
            # Create and show main window (Option B: Launch GUI and pass command)
            window = TapeciarniaApp()
            window.show()
            
            logging.info(f"Dispatching URI command: Action={action}, Params={params}")
            
            # This method will be implemented in ui/main_window.py
            window.handle_startup_uri(action, params)
            
            # Start the event loop and return immediately 
            
            return sys.exit(app.exec()) 
        else:
            # Parsing failed (e.g., bad format or scheme mismatch), fall through to normal launch
            logging.warning("URI command failed to parse. Proceeding to normal launch.")
    
    # 6. Normal Application Launch (Fallback Mode)

    # Create and show main window
    logging.debug("Creating main window")
    window = TapeciarniaApp()
    logging.debug("Showing main window")
    window.show()

    # Run the Qt event loop
    logging.info("Starting Qt event loop")
    try:
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Qt event loop failed: {e}")
        raise


if __name__ == "__main__":
    main()