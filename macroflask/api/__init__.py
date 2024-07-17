import os.path

from flask import Blueprint

from ..util.module_util import import_module_by_path_and_suffix_name

api_bp = Blueprint('api', __name__)

import_module_by_path_and_suffix_name(__file__, "_api")
