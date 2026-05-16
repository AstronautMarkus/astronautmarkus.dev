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

    # ── Storage ──────────────────────────────────────────────────
    # 'local' or 's3'
    STORAGE_DRIVER = os.getenv('STORAGE_DRIVER', 'local')
    STORAGE_LOCAL_ROOT = str(BASE_DIR / 'storage')

    # S3 / S3-compatible (MinIO, Cloudflare R2, DigitalOcean Spaces, …)
    STORAGE_S3_BUCKET = os.getenv('STORAGE_S3_BUCKET', '')
    STORAGE_S3_REGION = os.getenv('STORAGE_S3_REGION', 'us-east-1')
    STORAGE_S3_ACCESS_KEY = clean_env(os.getenv('STORAGE_S3_ACCESS_KEY'), '')
    STORAGE_S3_SECRET_KEY = clean_env(os.getenv('STORAGE_S3_SECRET_KEY'), '')
    # Optional: custom endpoint for S3-compatible services
    STORAGE_S3_ENDPOINT = clean_env(os.getenv('STORAGE_S3_ENDPOINT'), '')
    # Optional: override public base URL (e.g. a CDN in front of the bucket)
    STORAGE_S3_PUBLIC_URL = clean_env(os.getenv('STORAGE_S3_PUBLIC_URL'), '')