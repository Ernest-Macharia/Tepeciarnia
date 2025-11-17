import sys
import logging
import colorlog
from utils.system_utils import isBundle
# --- Custom Logging Handler for QListWidget ---

class InitLogging:
    def __init__(self):
        """
        Sets up the Python logging module, integrating configuration from a ConfigModel.
        This function configures logging to send messages to the QListWidget,
        an optional file, and/or the console (with optional color).
        """
        LOG_FILE_NAME = 'app.log'
        logging_style = True  # If True, use colored console output 
        
        # Get the root logger instance
        logger = logging.getLogger()
        if isBundle():
            logger.setLevel(logging.DEBUG)  # Set the base logging level
            LOGGING_MODE = 'both'  # Options: 'file', 'console', 'both'
        else:
            logger.setLevel(logging.DEBUG)  # Set the base logging level
            LOGGING_MODE = 'both'  # Options: 'file', 'console', 'both'

        # Clear any existing handlers to prevent duplicate log messages
        if logger.hasHandlers():
            logger.debug("Clearing existing logging handlers")
            logger.handlers.clear()

        # --- Define formatters ---
        # Basic formatter for file output and QListWidget (no color codes)
        basic_formatter = logging.Formatter(
            '[%(asctime)s][%(levelname)s]->%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console formatter (colored if logging_style is True, otherwise basic)
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s][%(filename)s][%(funcName)s]->%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            },
            secondary_log_colors={ # Optional: for coloring specific parts of the message
                'message': {
                    'ERROR': 'red',
                    'CRITICAL': 'bold_red',
                    'DEBUG': 'blue',
                    'INFO': 'white'
                }
            },
            style='%'
        )

        handlers_added = []

        # --- Conditionally add other handlers based on LOGGING_MODE ---
        if LOGGING_MODE in ['file', 'both']:
            try:
                file_handler = logging.FileHandler(LOG_FILE_NAME)
                file_handler.setFormatter(basic_formatter) # File logs typically don't need color
                logger.addHandler(file_handler)
                handlers_added.append(f"file handler ({LOG_FILE_NAME})")
            except Exception as e:
                print(f"Failed to setup file logging: {e}")

        if LOGGING_MODE in ['console', 'both']:
            try:
                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setFormatter(console_formatter)
                logger.addHandler(stream_handler)
                handlers_added.append("console handler")
            except Exception as e:
                print(f"Failed to setup console logging: {e}")

        if not handlers_added:
            logging.error("No logging handlers were successfully configured")
        else:
            logging.info(f"Logging setup completed successfully. Handlers: {', '.join(handlers_added)}")