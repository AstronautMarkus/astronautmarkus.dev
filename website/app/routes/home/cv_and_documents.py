from flask import render_template
from . import home_bp

@home_bp.route('/work-and-experience/cv-and-documents')
def cv_and_documents():
    return render_template('cv_and_documents.html')

@home_bp.route('/es/work-and-experience/cv-and-documents')
def cv_and_documents_es():
    return render_template('/es/cv_and_documents.html')