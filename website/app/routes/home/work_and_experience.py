from flask import render_template
from . import home_bp

@home_bp.route('/work-and-experience')
def work_and_experience():
    return render_template('work_and_experience.html')

@home_bp.route('/es/work-and-experience')
def work_and_experience_es():
    return render_template('/es/work_and_experience.html')