import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(dotenv_path=BASE_DIR / '.env')


def clean_env(value, default=''):
    if value is None:
        return default

    cleaned = str(value).strip()
    if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {'"', "'", '`'}:
        cleaned = cleaned[1:-1].strip()

    return cleaned


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
    DB_NAME = os.getenv('DB_NAME', 'flask_api_db')
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_TIMEOUT = float(os.getenv('MAIL_TIMEOUT', 10))
    # port 465 → implicit SSL; port 587 → STARTTLS; anything else → neither
    MAIL_USE_SSL = MAIL_PORT == 465
    MAIL_USE_TLS = MAIL_PORT == 587
    MAIL_USERNAME = clean_env(os.getenv('MAIL_USERNAME'), '')
    MAIL_PASSWORD = clean_env(os.getenv('MAIL_PASSWORD'), '')
    MAIL_DEFAULT_SENDER = MAIL_USERNAME