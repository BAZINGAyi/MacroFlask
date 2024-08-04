import logging
from typing import Union
from werkzeug.local import LocalProxy
from macroflask.util.light_logging import MacroFlaskLogger

"""
logging configuration start:
"""
logging_manager = MacroFlaskLogger()
_app_logger = None
_sys_logger = None
# If we don't use LocalProxy,
#   the app logger or sys logger will be initialized before the logging_manager is initialized,
#   but logger configuration is not loaded yet.
app_logger: Union[LocalProxy, logging.Logger] = LocalProxy(lambda: _get_app_logger())
sys_logger: Union[LocalProxy, logging.Logger] = LocalProxy(lambda: _get_sys_logger())


def _get_app_logger():
    global _app_logger
    if _app_logger is None:
        _app_logger = logging_manager.get_logger("app")  # 'app' is the logger name configured in the logging configuration
    return _app_logger


def _get_sys_logger():
    global _sys_logger
    if _sys_logger is None:
        _sys_logger = logging_manager.get_logger("sys")  # 'sys' is the logger name configured in the logging configuration
    return _sys_logger


# _logging_producer = None
# logging_producer = LocalProxy(lambda: _get_logging_producer())
# from macroflask.system.logging_produce import LoggingProducer
# def _get_logging_producer():
#     global _logging_producer
#     if _logging_producer is None:
#         _logging_producer = LoggingProducer(app_logger)
#     return _logging_producer

"""
logging configuration end.
"""