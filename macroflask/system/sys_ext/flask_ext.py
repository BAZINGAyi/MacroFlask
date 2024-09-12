import time
import traceback

from flask import request, g

from macroflask import ResponseHandler
from macroflask.util.os_util import UUIDUtil


class FlaskRequestMiddleware:
    def __init__(self, app=None, logger=None):
        if app is not None:
            self.app = app
            self.logger = logger

    def register_hooks(self):
        """Register before_request and after_request hooks."""
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
        self.app.errorhandler(Exception)(self.handle_exception)

    def before_request(self):
        """Called before each request to record the start time."""
        g.req_start_time = time.time()
        g.req_uuid = UUIDUtil.generate_uuid()

    def after_request(self, response):
        """Called after each request to calculate and print the elapsed time."""
        if hasattr(g, 'req_start_time'):
            total_time = time.time() - g.req_start_time
            api_name = request.endpoint  # Get the name of the API endpoint
            uuid = ""
            if hasattr(g, 'req_uuid'):
                uuid = g.req_uuid
            if self.logger:
                self.logger.info(f"=== {uuid} API {api_name} took {total_time:.4f} seconds.")

        return response

    def handle_exception(self, error):
        info = traceback.format_exc()
        if self.logger:
            self.logger.error(info)
        msg = ResponseHandler.convert_error_msg(error)
        return ResponseHandler.error(msg, status_code=500)
