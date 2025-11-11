import subprocess
import logging
import platform
import os

# Get logger for this module
logger = logging.getLogger(__name__)

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
    logger.debug(f"Starting blocking silent command: {command_parts}")
    logger.debug(f"Working directory: {cwd}, Timeout: {timeout}")
    
    if platform.system() != "Windows":
        logger.debug("Non-Windows platform, using standard subprocess.run")
        try:
            result = subprocess.run(command_parts, capture_output=True, text=True, cwd=cwd, timeout=timeout)
            logger.debug(f"Non-Windows command completed - returncode: {result.returncode}")
            return result
        except Exception as e:
            logger.error(f"Non-Windows command failed: {e}", exc_info=True)
            return None
    
    # --- Windows-Specific Execution (Blocking) ---
    logger.info(f"Executing Windows blocking command: {' '.join(command_parts)}")
    try:
        # Popen starts the process
        logger.debug("Creating subprocess with CREATE_NO_WINDOW flag")
        process = subprocess.Popen(
            command_parts,
            creationflags=CREATE_NO_WINDOW,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        logger.debug(f"Process created with PID: {process.pid}")

        # CRITICAL: communicate() waits for the process to terminate.
        logger.debug(f"Waiting for process completion with timeout: {timeout}")
        stdout, stderr = process.communicate(timeout=timeout)
        
        logger.info(f"Blocking command completed - PID: {process.pid}, returncode: {process.returncode}")
        logger.debug(f"Command stdout length: {len(stdout)}, stderr length: {len(stderr)}")
        
        if process.returncode != 0:
            logger.warning(f"Command returned non-zero exit code: {process.returncode}")
            if stderr:
                logger.warning(f"Command stderr: {stderr.strip()}")
        
        return subprocess.CompletedProcess(
            args=command_parts,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr
        )

    except FileNotFoundError as e:
        logger.error(f"Executable not found for command: {command_parts[0]}", exc_info=True)
        logger.error(f"Full command: {command_parts}")
        return None
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {' '.join(command_parts)}")
        if 'process' in locals():
            logger.warning(f"Terminating timed out process: {process.pid}")
            process.kill()
            try:
                process.wait(timeout=5)
                logger.debug("Timed out process terminated successfully")
            except subprocess.TimeoutExpired:
                logger.error("Failed to terminate timed out process")
        return None
    except Exception as e:
        logger.error(f"Unexpected error executing blocking command: {e}", exc_info=True)
        logger.error(f"Command that failed: {' '.join(command_parts)}")
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
    logger.debug(f"Starting non-blocking silent command: {command_parts}")
    logger.debug(f"Working directory: {cwd}")
    
    if platform.system() != "Windows":
        logger.debug("Non-Windows platform, using standard subprocess.Popen")
        try:
            process = subprocess.Popen(command_parts, cwd=cwd)
            logger.info(f"Non-Windows background process started - PID: {process.pid}")
            return process
        except Exception as e:
            logger.error(f"Non-Windows background process failed: {e}", exc_info=True)
            return None

    # --- Windows-Specific Execution (Non-Blocking) ---
    logger.info(f"Starting Windows non-blocking command: {' '.join(command_parts)}")
    try:
        # CRITICAL: Popen is used without communicate/wait. The process runs independently.
        logger.debug("Creating non-blocking subprocess with CREATE_NO_WINDOW flag")
        process = subprocess.Popen(
            command_parts,
            creationflags=CREATE_NO_WINDOW,
            cwd=cwd
        )
        logger.info(f"Background process started successfully - PID: {process.pid}")
        logger.debug(f"Process object created: {process}")
        return process
        
    except FileNotFoundError as e:
        logger.error(f"Executable not found for background command: {command_parts[0]}", exc_info=True)
        logger.error(f"Full background command: {command_parts}")
        return None
    except PermissionError as e:
        logger.error(f"Permission denied executing background command: {command_parts[0]}")
        logger.error(f"Full background command: {command_parts}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error starting background command: {e}", exc_info=True)
        logger.error(f"Command that failed: {' '.join(command_parts)}")
        return None


def terminate_process(process):
    """
    Safely terminate a process created by run_and_forget_silent
    
    Args:
        process: subprocess.Popen object to terminate
        
    Returns:
        bool: True if termination was successful, False otherwise
    """
    if process is None:
        logger.warning("Attempted to terminate None process")
        return False
        
    logger.info(f"Terminating process: {process.pid}")
    try:
        process.terminate()
        logger.debug(f"Terminate signal sent to process: {process.pid}")
        
        # Wait a bit for graceful termination
        try:
            process.wait(timeout=5)
            logger.info(f"Process terminated successfully: {process.pid}")
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"Process did not terminate gracefully, killing: {process.pid}")
            process.kill()
            process.wait()
            logger.info(f"Process killed: {process.pid}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to terminate process {process.pid}: {e}", exc_info=True)
        return False


def check_process_running(process):
    """
    Check if a process is still running
    
    Args:
        process: subprocess.Popen object to check
        
    Returns:
        bool: True if process is running, False otherwise
    """
    if process is None:
        return False
        
    return_code = process.poll()
    is_running = return_code is None
    
    logger.debug(f"Process {process.pid} running: {is_running}, returncode: {return_code}")
    return is_running


# --- Example Usage ---
if __name__ == "__main__":
    # Set up logging for example
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 1. Define the full path to your MPV executable
    # NOTE: Replace this placeholder path with your actual path
    mpv_path = r"C:\path\to\mpv.exe"  
    
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
             logger.warning("Please update the 'mpv_path' variable with your actual MPV executable location.")
        else:
            logger.info("Testing RUN MODE 1: Non-Blocking (AutoIt 'Run' Equivalent)")
            # This starts the process and returns immediately.
            # Use this for background tasks like starting MPV to play video.
            background_process = run_and_forget_silent(mpv_command) 
            
            if background_process:
                logger.info(f"MPV started in background with PID: {background_process.pid}")
                # If you needed to stop it later, you would use: background_process.terminate()

            logger.info("Testing RUN MODE 2: Blocking (Waits for completion)")
            # This is useful for running a utility command you need the output/result from.
            result = run_blocking_silent_command(["python", "--version"], timeout=5)

            if result and result.returncode == 0:
                logger.info("Blocking command successful.")
                logger.info(f"Python Version Info:\n{result.stdout.strip()}")
            elif result is not None:
                logger.warning(f"Blocking command failed (Return Code: {result.returncode})")
    else:
        logger.info("This script is designed for silent execution on Windows.")