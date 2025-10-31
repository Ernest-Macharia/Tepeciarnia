import subprocess
import sys
import platform
import os

# --- Constants for Windows-Specific Flags ---
# We use this to prevent the console window from showing up.
CREATE_NO_WINDOW = 0x08000000 

def run_blocking_silent_command(command_parts, cwd=None, timeout=None):
    """
    Executes a command on Windows silently, waits for it to complete, 
    and returns the result (blocking call).
    
    Args:
        command_parts (list): The command and its arguments as a list of strings.
        cwd (str, optional): The current working directory for the command.
        timeout (int, optional): The maximum time (in seconds) to wait for the command to finish.

    Returns:
        subprocess.CompletedProcess: An object containing the command result.
                                     Returns None if the platform is not Windows.
    """
    if platform.system() != "Windows":
        print(f"Warning: Silent execution flags are Windows-specific. Using standard run.")
        return subprocess.run(command_parts, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    
    # --- Windows-Specific Execution (Blocking) ---
    try:
        # Popen starts the process
        process = subprocess.Popen(
            command_parts,
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )

        # CRITICAL: communicate() waits for the process to terminate.
        stdout, stderr = process.communicate(timeout=timeout)
        
        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

    except FileNotFoundError:
        print(f"Error: Executable not found. Command: {command_parts[0]}")
        return None
    except subprocess.TimeoutExpired:
        print(f"Error: Command timed out after {timeout} seconds.")
        process.kill()
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def run_and_forget_silent(command_parts, cwd=None):
    """
    *** This is the Python equivalent of non-blocking AutoIt 'Run'. ***
    Executes a command on Windows silently and immediately returns 
    without waiting for the command to finish. The process runs in the background.

    Args:
        command_parts (list): The command and its arguments as a list of strings.
        cwd (str, optional): The current working directory for the command.

    Returns:
        subprocess.Popen or None: The process object if successful, None otherwise.
    """
    if platform.system() != "Windows":
        print("Warning: Silent execution flags are Windows-specific. Running standard Popen.")
        return subprocess.Popen(command_parts, cwd=cwd)

    try:
        # CRITICAL: Popen is used without communicate/wait. The process runs independently.
        process = subprocess.Popen(
            command_parts,
            creationflags=CREATE_NO_WINDOW,
            cwd=cwd
        )
        print(f"Successfully launched PID: {process.pid} in the background.")
        return process
    except FileNotFoundError:
        print(f"Error: Executable not found. Command: {command_parts[0]}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during silent run: {e}")
        return None


# --- Example Usage ---
if __name__ == "__main__":
    # 1. Define the full path to your MPV executable
    # NOTE: Replace this placeholder path with your actual path
    mpv_path = r"C:\path\to\mpv.exeqq"  
    
    # 2. Define the path to the video you want to play
    # NOTE: Replace this placeholder path with your video file
    video_file = os.path.join(os.getcwd(), "test_video.mp4") 

    # 3. Construct the command and arguments as a list
    mpv_command = [
        "notepad.exe",
        "utils.py"
    ]

    # Ensure we are on Windows before trying the silent feature
    if platform.system() == "Windows":
        
        if mpv_path == r"C:\path\to\mpv.exe":
             print("\n!!! WARNING !!!")
             print("Please update the 'mpv_path' variable in this script with your actual MPV executable location.")
        else:
            print("-" * 30)
            print("RUN MODE 1: Non-Blocking (AutoIt 'Run' Equivalent)")
            # This starts the process and returns immediately.
            # Use this for background tasks like starting MPV to play video.
            background_process = run_and_forget_silent(mpv_command) 
            
            if background_process:
                print(f"MPV started in background. You can continue running other code now.")
                # If you needed to stop it later, you would use: background_process.terminate()

            # print("-" * 30)
            # print("RUN MODE 2: Blocking (Waits for completion)")
            # # This is useful for running a utility command you need the output/result from.
            # result = run_blocking_silent_command([mpv_path, "--version"], timeout=5)

            # if result and result.returncode == 0:
            #     print("Blocking command successful.")
            #     print(f"MPV Version Info:\n{result.stdout.strip()}")
            # elif result is not None:
            #     print(f"Blocking command failed (Return Code: {result.returncode})")
    else:
        print("This script is designed for silent execution on Windows.")
