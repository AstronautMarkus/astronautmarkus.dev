from flask import Blueprint

home_bp = Blueprint('home', __name__)

from . import (
    index,
    about,
    markus_tech_stack,
    portfolio,
    work_and_experience,
    cv_and_documents,
    working_experience_data,
    external_links,
    contact,
    extras,
    notes,
)