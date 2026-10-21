import gzip
from datetime import datetime

from pymysql.converters import encoders, escape_sequence
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.models import Backup
from app.storage import storage

# Binary values as hex literals: PyMySQL's default bytes encoder emits raw
# bytes that would not survive the UTF-8 text dump.
_ENCODERS = {**encoders, bytes: lambda value, mapping=None: f"X'{value.hex()}'"}

# SQL_MODE reset (same as mysqldump) keeps the backslash escapes below valid
# on restore even if the target server runs with NO_BACKSLASH_ESCAPES.
_HEADER = (
    'SET NAMES utf8mb4;\n'
    'SET FOREIGN_KEY_CHECKS=0;\n'
    "SET SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n"
)
_FOOTER = 'SET FOREIGN_KEY_CHECKS=1;\n'


class BackupError(Exception):
    """Raised when a backup dump could not be generated."""


def generate_data_dump() -> bytes:
    """Build a gzip-compressed, data-only, row-per-INSERT SQL dump of the app
    database in Python (restore with `gunzip < dump.sql.gz | mysql <db>`).

    No table structure (schema is expected to already exist wherever the dump
    is restored), one row per INSERT so a human can read/diff the file, and
    every column named so the dump stays valid even if the target schema's
    column order differs slightly. Foreign key checks are disabled while
    restoring because tables are dumped in name order, not dependency order.
    """
    quote = db.engine.dialect.identifier_preparer.quote_identifier
    lines = [_HEADER]
    try:
        # One REPEATABLE READ transaction = one consistent snapshot across all
        # tables (what --single-transaction did); streamed so big tables don't
        # get buffered twice.
        with db.engine.connect().execution_options(
            isolation_level='REPEATABLE READ', stream_results=True
        ) as conn:
            for table in inspect(conn).get_table_names():
                result = conn.execute(text(f'SELECT * FROM {quote(table)}'))
                prefix = f"INSERT INTO {quote(table)} ({', '.join(map(quote, result.keys()))}) VALUES "
                lines.extend(
                    f'{prefix}{escape_sequence(row, "utf8mb4", _ENCODERS)};\n' for row in result
                )
    except SQLAlchemyError as exc:
        raise BackupError(f'Backup query failed: {exc}') from exc

    lines.append(_FOOTER)
    return gzip.compress(''.join(lines).encode('utf-8'))


def create_backup() -> Backup:
    """Generate a dump, store it via the configured storage driver (local or
    S3) and record it so it shows up in the admin backups list."""
    dump_bytes = generate_data_dump()
    filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql.gz"
    path = f'backups/{filename}'
    storage.put(path, dump_bytes, content_type='application/gzip')

    backup = Backup(filename=filename, file_path=path, size_bytes=len(dump_bytes))
    db.session.add(backup)
    db.session.commit()
    return backup
