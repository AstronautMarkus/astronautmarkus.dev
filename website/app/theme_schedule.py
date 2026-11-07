"""Weekly theme rotation for visitors who haven't picked a theme themselves.

The schedule is derived, not stored: every Monday-to-Sunday week maps to one
theme by cycling through the registered themes in order, so there is nothing
to maintain and every visitor sees the same theme in the same week.
"""
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
    SITE_TZ = ZoneInfo('America/Santiago')
except Exception:  # tzdata missing on slim images: UTC only shifts the week change by hours
    SITE_TZ = timezone.utc

# A Monday, so weeks counted from here line up with ISO weeks and the cycle
# doesn't stutter at year boundaries (ISO years have 52 or 53 weeks).
EPOCH = date(2024, 1, 1)


def today() -> date:
    return datetime.now(SITE_TZ).date()


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def theme_for_week(day: date, themes: list[str]) -> str:
    weeks_since_epoch = (week_start(day) - EPOCH).days // 7
    return themes[weeks_since_epoch % len(themes)]


def upcoming_weeks(themes: list[str], count: int = 12, start: date | None = None) -> list[dict]:
    """The current week followed by the next `count - 1`, each with its theme."""
    first = week_start(start or today())
    weeks = []
    for i in range(count):
        monday = first + timedelta(weeks=i)
        weeks.append({
            'start': monday,
            'end': monday + timedelta(days=6),
            'theme': theme_for_week(monday, themes),
            'current': i == 0,
        })
    return weeks
