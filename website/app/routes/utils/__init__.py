from flask import Blueprint

utils_bp = Blueprint('utils', __name__)

from . import cards, robots, visitor_counter