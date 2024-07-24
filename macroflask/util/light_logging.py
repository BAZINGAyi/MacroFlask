import logging
import logging.config
import os
import time
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler, TimedRotatingFileHandler
from multiprocessing import Queue
from flask import Flask


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
    def __init__(self, config, app=None, path=None):
        """
        Initialize the MacroFlaskLogger object.

        :param config: Configuration object.
        :param app: Flask application instance, used only in Flask environments.
        :param path: The path to the directory to store log files.

        """
        self.log_queue = Queue(-1)  # -1 means unlimited size
        self.logger_config = config
        self.path = path
        self.setup_logging()

    def setup_logging(self):
        logging.config.dictConfig(self.logger_config)
        self.queue_listener = CustomizeQueueListener(self.log_queue, *self.get_handlers())
        self.queue_listener.start()

    def get_handlers(self):
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
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(QueueHandler(self.log_queue))
        return logger

    def shutdown(self):
        self.queue_listener.stop()


def write_log(logger_type):
    from config import Config
    logger_manager = MacroFlaskLogger(Config.LOGGING)
    if logger_type == 0:
        app_logger = logger_manager.get_logger("app")
        app_logger.debug("2")
        app_logger.info("3")
        app_logger.warning("4")
        app_logger.error("5")
        app_logger.critical("6")

    elif logger_type == 1:
        sys_logger = logger_manager.get_logger("sys")
        sys_logger.debug("10")
        sys_logger.info("20")
        sys_logger.warning("30")
        sys_logger.error("40")
        sys_logger.critical("50")

    logger_manager.shutdown()


if __name__ == "__main__":
    from config import Config, get_config
    import threading
    # logger_manager = MacroFlaskLogger(Config)

    # def write_log(logger_type):
    #     if logger_type == 0:
    #         app_logger = logger_manager.get_logger("app")
    #         app_logger.debug("2")
    #         app_logger.info("3")
    #         app_logger.warning("4")
    #         app_logger.error("5")
    #         app_logger.critical("6")
    #
    #     elif logger_type == 1:
    #         sys_logger = logger_manager.get_logger("sys")
    #         sys_logger.debug("10")
    #         sys_logger.info("20")
    #         sys_logger.warning("30")
    #         sys_logger.error("40")
    #         sys_logger.critical("50")

    # # start multi-threading to test
    # threads = [threading.Thread(target=write_log, args=(index % 2,)) for index in range(100)]
    # for thread in threads:
    #     thread.start()
    #
    # # wait for all threads to finish
    # for thread in threads:
    #     thread.join()


    # start multi-processing to test

    while True:
        import multiprocessing
        processes = [multiprocessing.Process(target=write_log, args=(index % 2,)) for index in range(4)]
        for process in processes:
            process.start()

        for process in processes:
            process.join()

        time.sleep(20)
