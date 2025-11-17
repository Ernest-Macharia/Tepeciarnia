import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal, QStandardPaths
from PySide6.QtNetwork import QLocalServer, QLocalSocket

# --- DYNAMIC IMPORTS & CONTROLLER SETUP ---
# Attempt to import modules using both 'code' package structure (absolute)
# and relative structure to ensure compatibility in different environments.
try:
    # Absolute imports based on 'code' as top-level package
    from code.scripts.utils.path_utils import get_app_root, get_style_path
    from code.scripts.setLogging import InitLogging
    from code.scripts.utils.pathResolver import *
    from code.scripts.ui.main_window import TapeciarniaApp
    from code.scripts.ui import icons_resource_rc
    
    # URI Imports (Absolute)
    from code.scripts.utils.uri_handler import parse_uri_command
    
    logging.debug("Successfully imported modules using 'code' package structure")

except ImportError as e:
    logging.debug(f"Failed to import using 'code' package structure, trying relative imports: {e}")
    
    # Relative Imports
    from utils.path_utils import get_app_root, get_style_path
    # Relative Imports
    from utils.path_utils import get_app_root, get_style_path
    from setLogging import InitLogging
    from utils.pathResolver import *
    from ui.main_window import TapeciarniaApp
    from ui import icons_resource_rc
    
    # URI Imports (Relative)
    from utils.uri_handler import parse_uri_command
# --- END DYNAMIC IMPORTS ---

# Unique ID for the QLocalServer to prevent clashes
APP_ID_NAME = "Tapeciarnia_App_Instance_Lock_v1"

# --- Helper function to get the unique local server key ---
def get_local_server_key():
    """Generates a guaranteed unique path for the QLocalServer lock."""
    # Use the application data location for the lock to ensure it's user-specific and non-conflicting.
    local_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not local_dir:
        # Fallback if QStandardPaths fails (very rare)
        return APP_ID_NAME
    
    # Combine the directory with the app ID to create the unique key/path
    return os.path.join(local_dir, APP_ID_NAME)

class SingleApplication(QApplication):
    """
    Manages single-instancing using QLocalServer/QLocalSocket.
    If a second instance starts, it relays arguments to the first and exits.
    """
    message_received = Signal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self.is_primary_instance = False
        self.server_key = get_local_server_key() # <-- Use dynamic key
        self.server = QLocalServer(self)

        # 1. Attempt to start the server (become the primary instance)
        if self.server.listen(self.server_key):
            # Success: This is the primary instance.
            self.is_primary_instance = True
            self.server.newConnection.connect(self._handle_new_connection)
            logging.info(f"Primary instance started and listening on: {self.server_key}")
        else:
            # Failure: Server is already running OR the previous run crashed and left a lock file.
            
            # 2. Check for a persistent lock file and attempt cleanup
            if self.server.serverError() == QLocalServer.ServerError.AddressInUseError:
                logging.warning(f"Address '{self.server_key}' is in use. Attempting cleanup.")
                
                # Try to remove the old socket file/lock name
                QLocalServer.removeServer(self.server_key)
                
                # Try listening again after cleanup
                if self.server.listen(self.server_key):
                    # Success after cleanup: We are now the primary instance
                    self.is_primary_instance = True
                    self.server.newConnection.connect(self._handle_new_connection)
                    logging.info("Server lock file cleaned up. Primary instance started.")
                    return # Exit __init__ early to prevent secondary logic below

            # 3. If we failed to listen after cleanup, assume it's a running primary instance.
            if not self.is_primary_instance:
                logging.warning("Secondary instance detected. Attempting to send command to primary.")
                self._send_message_to_primary(argv)


    def _handle_new_connection(self):
        """Called when a secondary instance connects."""
        socket = self.server.nextPendingConnection()
        if socket:
            if socket.waitForReadyRead(2000): # Wait up to 2 seconds for data
                # Read all available data and decode it
                data = socket.readAll()
                message = str(data, 'utf-8')
                self.message_received.emit(message)
                logging.info(f"Primary instance received message from secondary: {message}")
            socket.disconnectFromServer()
            del socket

    def _send_message_to_primary(self, argv):
        """Sends command line arguments (URI) to the primary instance."""
        socket = QLocalSocket(self)
        socket.connectToServer(self.server_key) # <-- Use dynamic key
        
        if socket.waitForConnected(5000): # Wait up to 5 seconds
            # Only send the arguments (starting from sys.argv[1]), which includes the URI
            message = " ".join(argv[1:]) if len(argv) > 1 else ""
            socket.write(message.encode('utf-8'))
            socket.waitForBytesWritten(5000)
            socket.disconnectFromServer()
        else:
            # Fallback: If connection fails, something went wrong with the primary instance's lock.
            # We proceed as the primary instance to allow the app to launch.
            logging.error("Could not connect to primary instance. Starting anyway.")
            self.is_primary_instance = True


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
    # 1. Initialize logging
    # QCoreApplication must be created before any QObject or QWidget
    InitLogging()
    logging.info("Starting Tapeciarnia application")

    # 2. Create the SingleApplication instance
    # This automatically determines if it's primary or secondary
    app = SingleApplication(sys.argv)
    
    # If this is a secondary instance, it has already sent its arguments and should exit
    if not app.is_primary_instance:
        sys.exit(0)

    # --- PRIMARY INSTANCE EXECUTION BEGINS HERE ---
    
    # 3. Load stylesheet
    stylesheet_path = get_style_path(get_app_root())
    load_stylesheet(app, stylesheet_path)

    # 4. Create main window
    window = TapeciarniaApp()
    # Don't show immediately if we're launching via URI, as the URI handler might change state
    # window.show() 
    # window.setWindowState(Qt.WindowMinimized) # Start minimized or hidden if possible

    # 5. Connect signals for URI handling in the primary instance
    def dispatch_uri(uri_string):
        """Helper to parse and dispatch URI string from any source (startup or socket)."""
        # The secondary instance sends all command line arguments joined by a space.
        # We assume the first argument that starts with 'tapeciarnia:' is the URI.
        uri = next((arg for arg in uri_string.split() if arg.startswith('tapeciarnia:')), None)
        
        # Always show/raise the window when a command comes in, unless the command is silent
        window.showNormal() 
        window.activateWindow()

        if uri:
            logging.info(f"Dispatching received URI: {uri}")
            # Ensure the window is shown before attempting to display message boxes
            window.showNormal() 
            window.activateWindow()

            action, params = parse_uri_command(uri)
            if action:
                window.handle_startup_uri(action, params)
            else:
                logging.warning(f"URI command failed to parse: {uri}")
        else:
            # If no URI is found, simply raise the window to the foreground
            logging.info("Secondary instance launched without URI. Raising window.")

    # Connect message signal from secondary instances to the dispatch helper
    app.message_received.connect(dispatch_uri)

    # 6. Handle URI Launch (Initial startup)
    if len(sys.argv) > 1:
        # Pass all arguments to dispatch_uri to find the URI command
        dispatch_uri(" ".join(sys.argv[1:]))
    else:
        # If launched normally without a URI, show the window
        window.showNormal()
    
    # 7. Run the Qt event loop
    logging.info("Starting Qt event loop")
    try:
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Qt event loop failed: {e}")
        raise


if __name__ == "__main__":
    main()