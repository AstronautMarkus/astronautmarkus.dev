from flask import Blueprint

utils_bp = Blueprint('utils', __name__)

from . import robots, visitor_counter