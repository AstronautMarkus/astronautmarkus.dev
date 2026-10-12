"""
export_data_dump.py — Export all data in the database as a SQL dump (INSERT
statements only — no CREATE TABLE, no DROP TABLE, just the data).

Usage:
  # Writes to ./dumps/<db_name>_<timestamp>.sql (created if missing)
  python export_data_dump.py

  # Write to a specific path instead
  python export_data_dump.py --output /path/to/backup.sql
"""

import argparse
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.config.config import Config
from app.services.backup_service import BackupError, generate_data_dump

DEFAULT_DUMP_DIR = os.path.join(PROJECT_ROOT, 'dumps')


def export_dump(output_path=None):
    if output_path is None:
        os.makedirs(DEFAULT_DUMP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(DEFAULT_DUMP_DIR, f'{Config.DB_NAME}_{timestamp}.sql')

    print(f'[info] Dumping data from "{Config.DB_NAME}" @ {Config.DB_HOST}:{Config.DB_PORT} -> {output_path}')
    try:
        with create_app().app_context():
            dump = generate_data_dump()
    except BackupError as exc:
        print(f'[error] {exc}')
        sys.exit(1)

    with open(output_path, 'wb') as f:
        f.write(dump)

    print(f'[ok] Dump written to {output_path} ({len(dump)} bytes).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Export all data in the database as INSERT-only SQL statements (no CREATE TABLE).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--output', '-o', help='Path to write the .sql dump to. Defaults to ./dumps/<db>_<timestamp>.sql')
    args = parser.parse_args()

    export_dump(args.output)
