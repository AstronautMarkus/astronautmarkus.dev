import os
import sys
import xml.etree.ElementTree as ET

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.models import GuestbookEntry, PortfolioProject
from app.routes.utils import cards

HOSTILE = '<script>alert(1)</script> & "quotes" ' + 'x' * 120


def _check_svg(name, response):
    data = response.get_data()
    assert response.status_code == 200, f'{name}: HTTP {response.status_code}'
    assert response.mimetype == 'image/svg+xml', f'{name}: mimetype {response.mimetype}'
    ET.fromstring(data)  # GitHub shows a broken image for malformed SVG
    assert b'<script' not in data, f'{name}: user HTML not escaped'
    print(f'[OK]   {name} ({len(data)} bytes)')


def test_cards():
    app = create_app()
    client = app.test_client()
    for path in ('stats', 'latest-post', 'posts', 'guestbook'):
        _check_svg(path, client.get(f'/card/{path}.svg'))

    # Hostile rows inside a transaction that is rolled back, never committed.
    with app.test_request_context('/'):
        project = PortfolioProject(title=HOSTILE[:200], description=HOSTILE, github_repo_url='https://github.com/' + 'a' * 80)
        entry = GuestbookEntry(name=HOSTILE[:100], message=HOSTILE, approved=True)
        db.session.add_all([project, entry])
        db.session.flush()
        try:
            _check_svg('project (hostile)', cards.card_project(project.id))
            _check_svg('guestbook (hostile)', cards.card_guestbook())
        finally:
            db.session.rollback()

    assert client.get('/card/project/999999999.svg').status_code == 404
    print('[OK]   missing project → 404')
    page = client.get('/widgets')
    assert page.status_code == 200 and b'/card/stats.svg' in page.data, 'widgets page'
    print('[OK]   /widgets')


if __name__ == '__main__':
    test_cards()
