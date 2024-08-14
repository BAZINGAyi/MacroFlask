import logging
import logging.config
import os
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler, TimedRotatingFileHandler
from multiprocessing import Queue


class CustomizeQueueListener(QueueListener):

    def handle(self, record):
        """
        Handle a record.

        This just loops through the handlers offering them the record
        to handle.
        """
        record = self.prepare(record)
        for handler in self.handlers:
            if not self.respect_handler_level:
                process = True
            else:
                process = record.levelno >= handler.level

            if handler.__class__.__name__ in ['RotatingFileHandler', 'TimedRotatingFileHandler']:
                handler_file_name = handler.baseFilename
                record_name = record.name
                if record_name in handler_file_name:
                    process = True
                else:
                    process = False

            if process:
                handler.handle(record)


class MacroFlaskLogger:
    def __init__(self, config=None, app=None, path=None):
        """
        Initialize the MacroFlaskLogger object.

        :param config: Configuration object.
        :param app: Flask application instance, used only in Flask environments.
        :param path: The path to the directory to store log files.

        """
        self.log_queue = Queue(-1)  # -1 means unlimited size
        self.logger_config = config
        self.path = path
        if config:
            self._setup_logging()

    def init_flask_logger(self, config, app, path):
        self.logger_config = config
        self.path = path
        self._setup_logging()

    def _setup_logging(self):
        # logging.config.dictConfig(self.logger_config)
        self.queue_listener = CustomizeQueueListener(self.log_queue, *self._get_handlers())
        self.queue_listener.start()

    def _get_handlers(self):
        handlers = []
        for handler_name, handler_config in self.logger_config['handlers'].items():
            handler_class = self._get_handler_class(handler_config['class'])
            handler = self._create_handler(handler_class, handler_config)

            # Set level if specified
            if 'level' in handler_config:
                handler.setLevel(handler_config['level'])

            # Set formatter if specified
            if 'formatter' in handler_config:
                formatter_name = handler_config['formatter']
                formatter_config = self.logger_config['formatters'][formatter_name]
                formatter = logging.Formatter(formatter_config['format'])
                handler.setFormatter(formatter)

            handlers.append(handler)
        return handlers

    def _get_handler_class(self, handler_class_str):
        """
        Return the handler class based on the handler class string.

        :param handler_class_str: The string of the handler class.
        :return: The handler class.
        """
        if handler_class_str == 'logging.StreamHandler':
            return logging.StreamHandler

        elif handler_class_str == 'logging.handlers.RotatingFileHandler':
            return RotatingFileHandler

        elif handler_class_str == 'logging.handlers.TimedRotatingFileHandler':
            return TimedRotatingFileHandler

        else:
            raise ValueError(f"Unsupported handler class: {handler_class_str}")

    def _create_handler(self, handler_class, handler_config):
        """
        Create and return the handler instance.

        :param handler_class: The handler class.
        :param handler_config: The handler configuration dictionary.
        :return: The handler instance.
        """
        # Filter out 'class' and any other handler-specific keys
        filtered_config = {k: v for k, v in handler_config.items() if
                           k not in ['class', 'formatter', 'level']}

        # Create the handler with the appropriate parameters
        if issubclass(handler_class, (RotatingFileHandler, TimedRotatingFileHandler)):
            # add encoding='utf-8' to avoid UnicodeEncodeError
            filtered_config['encoding'] = 'utf-8'

            if 'filename' not in filtered_config:
                raise ValueError(f"'filename' is required for handler {handler_class.__name__}")
            if self.path:
                filtered_config['filename'] = os.path.join(self.path, filtered_config['filename'])
            return handler_class(**filtered_config)

        elif issubclass(handler_class, logging.StreamHandler):
            return handler_class(**filtered_config)

        else:
            raise ValueError(f"Unsupported handler class: {handler_class}")

    def get_logger(self, name):
        """
        Return a logger with the specified name.

        Note:
        This method should be called after init_flask_logger() and only call this method once.

        :param name:  The name of the logger.

        :return:  The logger instance.
        """
        if not self.logger_config:
            raise ValueError("Logger configuration is not set. Please call init_flask_logger() first.")

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(QueueHandler(self.log_queue))
        return logger

    def shutdown(self):
        self.queue_listener.stop()
