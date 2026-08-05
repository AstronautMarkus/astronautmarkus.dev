from flask import Blueprint

kanarianlintu_bp = Blueprint('kanarianlintu', __name__)

from . import server, env, fail