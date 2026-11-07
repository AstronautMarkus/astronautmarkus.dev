from app.routes.main import main_bp
from app import render_localized_template, THEMES, theme_schedule


@main_bp.route('/themes/calendar')
def theme_calendar():
    weeks = theme_schedule.upcoming_weeks(list(THEMES))
    return render_localized_template('main/theme_calendar.html', weeks=weeks)
