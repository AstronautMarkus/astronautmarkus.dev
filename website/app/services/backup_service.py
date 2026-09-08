import os
import shutil
import subprocess

from flask import current_app

DUMP_TIMEOUT_SECONDS = 300


class BackupError(Exception):
    """Raised when a backup dump could not be generated."""


def generate_data_dump() -> bytes:
    """Run mysqldump for a data-only, row-per-INSERT dump of the app database.

    --no-create-info drops table structure (schema is expected to already exist
    wherever the dump is restored), --extended-insert=FALSE keeps one row per
    INSERT statement so a human can read/diff the file, and --complete-insert
    names every column so the dump stays valid even if the target schema's
    column order differs slightly.
    """
    binary = shutil.which('mysqldump')
    if not binary:
        raise BackupError('mysqldump is not installed on this server.')

    cfg = current_app.config
    args = [
        binary,
        '--no-create-info',
        '--single-transaction',
        '--complete-insert',
        '--extended-insert=FALSE',
        '--skip-triggers',
        '--skip-comments',
        '--host', str(cfg['DB_HOST']),
        '--port', str(cfg['DB_PORT']),
        '--user', str(cfg['DB_USER']),
        str(cfg['DB_NAME']),
    ]
    env = {**os.environ, 'MYSQL_PWD': str(cfg['DB_PASSWORD'])}

    try:
        result = subprocess.run(
            args,
            env=env,
            capture_output=True,
            timeout=DUMP_TIMEOUT_SECONDS,
            check=True,
        )
    except FileNotFoundError as exc:
        raise BackupError('mysqldump is not installed on this server.') from exc
    except subprocess.TimeoutExpired as exc:
        raise BackupError('Backup timed out.') from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode('utf-8', errors='replace').strip() if exc.stderr else ''
        raise BackupError(f'mysqldump failed: {stderr or "unknown error"}') from exc

    if not result.stdout:
        raise BackupError('mysqldump produced an empty dump.')

    return result.stdout
