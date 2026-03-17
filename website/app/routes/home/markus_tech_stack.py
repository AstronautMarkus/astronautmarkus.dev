
from flask import render_template
from . import home_bp
from app.models.models import TechStack
from collections import defaultdict


def type_priority(type_name):
    normalized = (type_name or '').strip().lower()
    if normalized == 'front end':
        return 0
    if normalized == 'back end':
        return 1
    if normalized == 'database / cache':
        return 2
    if normalized == 'devops':
        return 3
    return 99


def get_techstack_by_type():
    techstack = TechStack.query.all()
    techstack.sort(key=lambda tech: (type_priority(tech.type), (tech.type or '').lower(), (tech.name or '').lower()))
    grouped = defaultdict(list)
    for tech in techstack:
        grouped[tech.type].append(tech)
    return dict(grouped)

@home_bp.route('/markus-tech-stack')
def markus_tech_stack():
    return render_template('/home/markus_tech_stack.html', techstack_by_type=get_techstack_by_type())

@home_bp.route('/es/markus-tech-stack')
def markus_tech_stack_es():
    return render_template('/home/es/markus_tech_stack.html', techstack_by_type=get_techstack_by_type())