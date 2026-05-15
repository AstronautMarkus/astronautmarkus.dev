import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app
from app.models.models import db


def init_database():
    app = create_app()
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Done.")


def reset_database():
    app = create_app()
    with app.app_context():
        print("Dropping tables...")
        db.drop_all()
        print("Recreating tables...")
        db.create_all()
        print("Done.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        reset_database()
    else:
        init_database()