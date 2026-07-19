import random
from datetime import datetime, timezone

from app.routes.main import main_bp
from app.i18n import get_current_language, render_localized_template

BIRTH_DATETIME = datetime(2003, 3, 16, tzinfo=timezone.utc)


def _geek_age_variants():
    """(english, spanish) pairs describing the same underlying age metric, so both
    locales stay in sync even though only one is picked per request."""
    now = datetime.now(timezone.utc)
    delta = now - BIRTH_DATETIME
    seconds = delta.total_seconds()
    days = delta.days
    years = seconds / (365.2425 * 86400)
    whole_years = int(years)
    birth_unix = int(BIRTH_DATETIME.timestamp())

    return [
        (f"{seconds:,.0f} seconds old", f"{seconds:,.0f} segundos de vida"),
        (f"{seconds / 60:,.0f} minutes old", f"{seconds / 60:,.0f} minutos de vida"),
        (f"{seconds / 3600:,.0f} hours old", f"{seconds / 3600:,.0f} horas de vida"),
        (f"{days:,} days old", f"{days:,} días de vida"),
        (f"{days // 7:,} weeks old", f"{days // 7:,} semanas de vida"),
        (f"{int(years * 12):,} months old", f"{int(years * 12):,} meses de vida"),
        (f"0b{whole_years:b} in binary", f"0b{whole_years:b} en binario"),
        (f"0x{whole_years:X} in hex", f"0x{whole_years:X} en hexadecimal"),
        (f"{years:.6f} trips around the sun", f"{years:.6f} vueltas alrededor del sol"),
        (f"{years:.4f}% of a century", f"{years:.4f}% de un siglo"),
        (f"born at unix time {birth_unix:,}", f"nacido en el tiempo unix {birth_unix:,}"),
        (f"{seconds:.3e} seconds (scientific notation)", f"{seconds:.3e} segundos (notación científica)"),
        ("still compiling...", "todavía compilando..."),
        ("classified — access denied (403)", "clasificado — acceso denegado (403)"),
        (
            f"{whole_years} — but that's just a lossy cache of the real number",
            f"{whole_years} — pero eso es solo una caché con pérdida del número real",
        ),
    ]


@main_bp.route('/profile')
def profile():
    en_age, es_age = random.choice(_geek_age_variants())
    age_geek = en_age if get_current_language() == 'en' else es_age
    return render_localized_template('main/profile.html', age_geek=age_geek)
