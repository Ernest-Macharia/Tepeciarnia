import sys
import logging # Import the logging module
import colorlog # Import colorlog for colored console output
# --- Custom Logging Handler for QListWidget ---


class InitLogging:
    def _init_(self):
        """
        Sets up the Python logging module, integrating configuration from a ConfigModel.
        This function configures logging to send messages to the QListWidget,
        an optional file, and/or the console (with optional color).
        """
        LOG_FILE_NAME = 'app.log'
        LOGGING_MODE = 'both'  # Options: 'file', 'console', 'both'
        logging_style = True  # If True, use colored console output 
        # get instance of log window
        # Get the root logger instance
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)  # Set the base logging level

        # Clear any existing handlers to prevent duplicate log messages
        if logger.hasHandlers():
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


        # --- Conditionally add other handlers based on LOGGING_MODE ---
        if LOGGING_MODE in ['file', 'both']:
            file_handler = logging.FileHandler(LOG_FILE_NAME)
            file_handler.setFormatter(basic_formatter) # File logs typically don't need color
            logger.addHandler(file_handler)

        if LOGGING_MODE in ['console', 'both']:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(console_formatter)
            logger.addHandler(stream_handler)

        logging.debug("Logging setup successful") # Log the successful setup