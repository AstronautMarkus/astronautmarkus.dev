"""
export_data_dump.py — Export all data in the database as a gzip-compressed SQL
dump (INSERT statements only — no CREATE TABLE, no DROP TABLE, just the data).

Usage:
  # Stores backups/backup_<timestamp>.sql.gz in the app's storage driver
  # (local or S3, per STORAGE_DRIVER in .env) and lists it in the admin panel
  python export_data_dump.py

  # Write to a specific local path instead
  python export_data_dump.py --output /path/to/backup.sql.gz

Restore with:
  gunzip < backup.sql.gz | mysql <db_name>
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.config.config import Config
from app.services.backup_service import BackupError, create_backup, generate_data_dump


def export_dump(output_path=None):
    app = create_app()
    target = output_path or f"{app.config.get('STORAGE_DRIVER', 'local')} storage"
    print(f'[info] Dumping data from "{Config.DB_NAME}" @ {Config.DB_HOST}:{Config.DB_PORT} -> {target}')
    try:
        with app.app_context():
            if output_path is None:
                backup = create_backup()
                print(f'[ok] Dump stored at {backup.file_path} ({backup.size_bytes} bytes).')
                return
            dump = generate_data_dump()
    except BackupError as exc:
        print(f'[error] {exc}')
        sys.exit(1)

    with open(output_path, 'wb') as f:
        f.write(dump)

    print(f'[ok] Dump written to {output_path} ({len(dump)} bytes).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Export all data in the database as gzip-compressed, INSERT-only SQL statements (no CREATE TABLE).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--output', '-o', help='Local path to write the .sql.gz dump to. Defaults to the app storage (local or S3).')
    args = parser.parse_args()

    export_dump(args.output)
