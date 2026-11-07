"""Pull external data (YouTube, GitHub) into the database. Run hourly by cron/astronautmarkus_sync.

    python app/scripts/sync.py            # every source
    python app/scripts/sync.py github     # just one
"""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.services.github_service import sync_github
from app.services.youtube_service import sync_videos

JOBS = {'youtube': sync_videos, 'github': sync_github}


def main(sources):
    unknown = set(sources) - JOBS.keys()
    if unknown:
        print(f"unknown source(s) {', '.join(sorted(unknown))}; pick from {', '.join(JOBS)}", file=sys.stderr)
        return 2

    failed = []
    with create_app().app_context():
        for name in sources or JOBS:
            try:
                print(f'[{name}] ok: {JOBS[name]()}')
            except Exception as exc:  # one broken source must not stop the others; exit code still reports it
                db.session.rollback()
                failed.append(name)
                print(f'[{name}] failed: {exc}', file=sys.stderr)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
