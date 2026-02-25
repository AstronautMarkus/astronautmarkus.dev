from flask import Blueprint

home_bp = Blueprint('home', __name__)

from . import index, about, markus_tech_stack, portfolio