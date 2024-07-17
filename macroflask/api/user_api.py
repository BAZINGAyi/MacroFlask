from flask import abort
from jinja2 import TemplateNotFound
from . import api_bp


@api_bp.route('/user/')
def show():
    try:
        return "Hello, World!" + str(12222)
    except TemplateNotFound:
        abort(404)