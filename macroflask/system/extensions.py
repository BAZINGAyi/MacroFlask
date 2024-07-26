from flask_jwt_extended import JWTManager

import logging
from typing import Union
from werkzeug.local import LocalProxy
from macroflask.util.light_logging import MacroFlaskLogger

# jwt
jwt_manager = JWTManager()

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
        _app_logger = logging_manager.get_logger("app") # 'app' is the logger name configured in the logging configuration
    return _app_logger


def _get_sys_logger():
    global _sys_logger
    if _sys_logger is None:
        _sys_logger = logging_manager.get_logger("sys") # 'sys' is the logger name configured in the logging configuration
    return _sys_logger

"""
logging configuration end.
"""