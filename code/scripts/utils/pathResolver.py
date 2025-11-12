
import sys
import os
from pathlib import Path


def get_app_root():
    """
    Determines the path of the running application/script's directory, 
    handling both source code and bundled executables (PyInstaller/cx_Freeze).
    """
    # 1. Check for 'frozen' status (indicates a bundled executable)
    if getattr(sys, 'frozen', False):
        # If frozen, sys.executable is the path to the app file itself.
        base_path = Path(sys.executable).resolve()
    else:
        # If not frozen, we use the path of the script that started the app.
        base_path = Path(sys.argv[0]).resolve()
        
    # We return the directory containing the executable or the script.
    return str(base_path.parent) 

def get_mpv_path(base_path:str) -> str:
    return os.path.join(base_path,"bin","mpv","mpv.exe")

def get_weebp_path(base_path:str) -> str:
    return os.path.join(base_path,"bin","weebp","weebp.exe")

def get_style_path(base_path:str):
    return os.path.join(base_path,"ui","style","style.qss")

__all__ = ["get_app_root","get_weebp_path","get_mpv_path","get_style_path"]
