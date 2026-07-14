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
import shutil
import subprocess
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, PROJECT_ROOT)

from app.config.config import Config

DEFAULT_DUMP_DIR = os.path.join(PROJECT_ROOT, 'dumps')


def export_dump(output_path=None):
    if not shutil.which('mysqldump'):
        print('[error] "mysqldump" was not found on PATH.')
        sys.exit(1)

    if output_path is None:
        os.makedirs(DEFAULT_DUMP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = os.path.join(DEFAULT_DUMP_DIR, f'{Config.DB_NAME}_{timestamp}.sql')

    cmd = [
        'mysqldump',
        '--host', Config.DB_HOST,
        '--port', str(Config.DB_PORT),
        '--user', Config.DB_USER,
        '--no-create-info',       # data only, no CREATE TABLE
        '--skip-add-drop-table',  # no DROP TABLE either
        '--complete-insert',      # INSERT INTO table (col1, col2, ...) — safe to replay elsewhere
        '--single-transaction',   # consistent snapshot, no table locking
        Config.DB_NAME,
    ]

    env = os.environ.copy()
    env['MYSQL_PWD'] = Config.DB_PASSWORD  # avoids leaking the password via `-p` in the process list

    print(f'[info] Dumping data from "{Config.DB_NAME}" @ {Config.DB_HOST}:{Config.DB_PORT} -> {output_path}')
    with open(output_path, 'w') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, text=True)

    if result.returncode != 0:
        os.remove(output_path)
        print(f'[error] mysqldump failed:\n{result.stderr}')
        sys.exit(1)

    print(f'[ok] Dump written to {output_path} ({os.path.getsize(output_path)} bytes).')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Export all data in the database as INSERT-only SQL statements (no CREATE TABLE).',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument('--output', '-o', help='Path to write the .sql dump to. Defaults to ./dumps/<db>_<timestamp>.sql')
    args = parser.parse_args()

    export_dump(args.output)
