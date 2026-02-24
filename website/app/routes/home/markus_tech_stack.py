
from flask import render_template
from . import home_bp
from app.models.models import TechStack
from collections import defaultdict

@home_bp.route('/markus-tech-stack')
def markus_tech_stack():
    techstack = TechStack.query.all()

    def type_priority(type_name):
        normalized = (type_name or '').strip().lower()
        if 'front' in normalized:
            return 0
        if 'back' in normalized:
            return 1
        if 'database' in normalized:
            return 2
        if 'devops' in normalized:
            return 3
        return 99

    techstack.sort(key=lambda tech: (type_priority(tech.type), (tech.type or '').lower(), (tech.name or '').lower()))
    techstack_by_type = defaultdict(list)

    for tech in techstack:
        techstack_by_type[tech.type].append(tech)

    return render_template('markus_tech_stack.html', techstack_by_type=dict(techstack_by_type))