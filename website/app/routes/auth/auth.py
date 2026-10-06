from flask import redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.i18n import render_localized_template
from app.models.models import User
from app.routes.auth import auth_bp
from app.utils import safe_redirect_target


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(safe_redirect_target(request.args.get('next'), url_for('admin.dashboard')))

        flash('invalid_credentials', 'error')

    return render_localized_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
