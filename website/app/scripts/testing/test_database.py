import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from sqlalchemy import text
from app import create_app, db


def test_database():
    app = create_app()
    with app.app_context():
        host   = app.config['DB_HOST']
        port   = app.config['DB_PORT']
        name   = app.config['DB_NAME']
        user   = app.config['DB_USER']

        print(f"Host    : {host}:{port}")
        print(f"Database: {name}")
        print(f"User    : {user}")
        print()

        try:
            db.session.execute(text("SELECT 1"))
            print("[OK] Database connection successful.")
        except Exception as e:
            print(f"[FAIL] {type(e).__name__}: {e}")
            sys.exit(1)

        try:
            tables = db.engine.dialect.get_table_names(db.engine.connect())
            if tables:
                print(f"[OK] Tables found: {', '.join(tables)}")
            else:
                print("[--] No tables found — run create_db.py to initialise the schema.")
        except Exception as e:
            print(f"[WARN] Could not list tables: {e}")


if __name__ == "__main__":
    test_database()
