# app.py

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from ui.mainUI import Ui_MainWindow
from utils.pathResolver import *
from ui import icons_rc 
from core.handle_drops import DropTargetFrame
def load_stylesheet(app_instance, filepath):
    """Opens a QSS/CSS file and applies its content as a stylesheet to the QApplication."""
    try:
        with open(filepath, "r") as f:
            # Read the entire file content
            stylesheet = f.read()
            # Apply the stylesheet to the entire application
            app_instance.setStyleSheet(stylesheet)
            print(f"Successfully loaded stylesheet from: {filepath}")
    except FileNotFoundError:
        print(f"Error: Stylesheet file not found at {filepath}")
        
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)


    def browesFiles(self):
        pass
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # --- The crucial step ---
    # Call the function to load and apply your external style file
    load_stylesheet(app, get_style_path(get_app_root())) 
    
    # Now run your application
    window = MainWindow()
    window.show()
    sys.exit(app.exec())