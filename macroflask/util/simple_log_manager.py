# simple_log_manager.py
import os

from loguru import logger as ru_logger


class LogManager:
    def __init__(self, config, enqueue=False):
        """Initialize the LogManager with a given configuration object."""
        self.config = config
        self.enqueue = enqueue

        # Set up loggers based on the configuration
        self.setup_loggers()

    def setup_loggers(self):
        """Set up log handlers according to the configuration."""
        # if current os platform is windows and multiprocessing mode, need to execute ru_logger.remove() before add
        if os.name == 'nt' and self.enqueue:
            ru_logger.remove() # "sys.stderr" sink is not picklable

        for log_id, levels in self.config.items():
            for level_id, settings in levels.items():
                filename = settings["filename"]
                log_format = settings["format"]
                rotate = settings.get("rotate")  # Get rotate value, if any

                # Add a handler for each log level within the log type
                ru_logger.add(
                    filename,
                    level=level_id.upper(),
                    # Infer level from the key (e.g., "info" becomes "INFO")
                    format=log_format,
                    filter=self.create_filter(log_id),
                    rotation=rotate,  # Use 'rotation' for log file rotation
                    enqueue=self.enqueue  # Enable asynchronous writing
                )

                # Dynamically create corresponding log attributes with bound parameters
                bind_params = {log_id: True}
                setattr(self, f"{log_id}_log", ru_logger.bind(**bind_params))

    """
    Due to the inability to pickle nested functions in multiprocessing mode, 
    so it is not possible to dynamically create filters based on the configuration file.
    
    Therefore, two filters need to be created in the LogManager class to distinguish different log records.
    """

    def app_filter(self, record):
        return "app_log" in record["extra"]

    def sys_filter(self, record):
        return "sysLog" in record["extra"]

    def create_filter(self, log_id):
        """Dynamically create a filter based on the log identifier."""

        if log_id == "app_log":
            return self.app_filter
        elif log_id == "sys_log":
            return self.sys_filter
        else:
            raise ValueError(f"Unknown log identifier: {log_id}")

    def get_logger(self, log_id):
        """Return the logger instance for the specified log identifier and level."""
        return getattr(self, f"{log_id}_log", None)

    def get_raw_logger(self):
        return ru_logger
