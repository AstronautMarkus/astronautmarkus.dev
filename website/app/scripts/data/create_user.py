"""
create_user.py — Create a user in the database.

Usage:
  # Interactive CLI
  python create_user.py

  # Non-interactive (flags)
  python create_user.py --username admin --password secret123
  python create_user.py --username admin --password secret123 --email admin@example.com
"""

import os
import sys
import argparse
import getpass

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app import create_app
from app.models.models import db, User


MIN_PASSWORD_LENGTH = 8


def validate_username(username):
    if not username or not username.strip():
        raise ValueError("Username cannot be empty.")
    if len(username.strip()) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if len(username.strip()) > 80:
        raise ValueError("Username must be 80 characters or fewer.")
    return username.strip()


def validate_password(password):
    if not password:
        raise ValueError("Password cannot be empty.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return password


def validate_email(email):
    if not email or not email.strip():
        return None
    email = email.strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Invalid email address.")
    if len(email) > 120:
        raise ValueError("Email must be 120 characters or fewer.")
    return email


def create_user(username, password, email=None):
    app = create_app()
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"[error] Username '{username}' already exists.")
            sys.exit(1)

        if email and User.query.filter_by(email=email).first():
            print(f"[error] Email '{email}' is already in use.")
            sys.exit(1)

        user = User(
            username=username,
            email=email or f"{username}@localhost",
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        print(f"[ok] User '{username}' created successfully.")


def interactive_mode():
    print("=== Create User ===")
    print("Press Ctrl+C at any time to cancel.\n")

    try:
        # Username
        while True:
            try:
                raw = input("Username: ")
                username = validate_username(raw)
                break
            except ValueError as e:
                print(f"  [!] {e}")

        # Email (optional)
        while True:
            try:
                raw = input("Email (optional, press Enter to skip): ").strip()
                email = validate_email(raw) if raw else None
                break
            except ValueError as e:
                print(f"  [!] {e}")

        # Password (hidden input, confirmed)
        while True:
            try:
                password = getpass.getpass("Password: ")
                validate_password(password)
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("  [!] Passwords do not match.")
                    continue
                break
            except ValueError as e:
                print(f"  [!] {e}")

    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)

    create_user(username, password, email)


def flags_mode(args):
    try:
        username = validate_username(args.username)
        password = validate_password(args.password)
        email = validate_email(args.email) if args.email else None
    except ValueError as e:
        print(f"[error] {e}")
        sys.exit(1)

    create_user(username, password, email)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create a user in the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--username", help="Username for the new user.")
    parser.add_argument("--password", help="Password for the new user.")
    parser.add_argument("--email", help="Email address (optional).")

    args = parser.parse_args()

    if args.username or args.password:
        # Flags mode: both --username and --password are required together
        if not args.username or not args.password:
            parser.error("--username and --password must both be provided.")
        flags_mode(args)
    else:
        interactive_mode()
