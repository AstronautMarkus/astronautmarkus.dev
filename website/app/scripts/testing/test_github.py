import os
import sys
from datetime import date, timedelta

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from app import create_app, db
from app.models.models import SyncedSnapshot
from app.services.github_service import GithubSyncError, _streaks, parse_user

HOSTILE = '<script>alert(1)</script> & "quotes"'


def _user(counts=(0, 3, 0, 5, 7, 1, 0, 2, 4)):
    """Minimal GraphQL `user` answer: one partial week then full ones, starting on a Thursday."""
    first = date(2026, 1, 1)  # a Thursday: the first week holds Thu-Sat only
    days = [{'date': (first + timedelta(i)).isoformat(), 'contributionCount': c,
             'contributionLevel': 'FOURTH_QUARTILE' if c > 4 else 'FIRST_QUARTILE' if c else 'NONE'}
            for i, c in enumerate(counts)]
    return {
        'repositories': {'totalCount': 43, 'nodes': [
            {'languages': {'edges': [{'size': 750, 'node': {'name': 'Python', 'color': '#3572A5'}},
                                     {'size': 250, 'node': {'name': 'CSS', 'color': None}}]}},
        ]},
        'pinnedItems': {'nodes': [
            {'name': 'payday-bank', 'description': HOSTILE, 'url': 'https://github.com/AstronautMarkus/payday-bank',
             'stargazerCount': 2, 'primaryLanguage': {'name': 'Python', 'color': '#3572A5'}},
        ]},
        'contributionsCollection': {
            'totalCommitContributions': 20, 'totalPullRequestContributions': 3,
            'contributionCalendar': {'totalContributions': sum(counts),
                                     'weeks': [{'contributionDays': days[:3]}, {'contributionDays': days[3:]}]},
        },
    }


def _expect_rejected(name, mutate):
    user = _user()
    mutate(user)
    try:
        parse_user(user)
    except GithubSyncError:
        print(f'[OK]   rejects {name}')
    else:
        raise AssertionError(f'accepted {name}')


def test_parse():
    data = parse_user(_user())
    assert data['contributions'] == 22 and data['public_repos'] == 43
    assert [len(w) for w in data['weeks']] == [3, 6]
    assert data['weeks'][1][1] == ['2026-01-05', 7, 4]
    assert data['languages'] == [{'name': 'Python', 'color': '#3572A5', 'pct': 75.0},
                                 {'name': 'CSS', 'color': None, 'pct': 25.0}]
    assert (data['current_streak'], data['longest_streak']) == (2, 3)
    print('[OK]   parses a valid answer')

    _expect_rejected('negative counts', lambda u: u['contributionsCollection'].update(totalCommitContributions=-1))
    _expect_rejected('bools as counts', lambda u: u['repositories'].update(totalCount=True))
    _expect_rejected('a javascript: repo URL', lambda u: u['pinnedItems']['nodes'][0].update(url='javascript:alert(1)'))
    _expect_rejected('an unknown level', lambda u: u['contributionsCollection']['contributionCalendar']['weeks'][0]
                     ['contributionDays'][0].update(contributionLevel='OVER_9000'))
    _expect_rejected('a bad date', lambda u: u['contributionsCollection']['contributionCalendar']['weeks'][0]
                     ['contributionDays'][0].update(date='yesterday'))
    _expect_rejected('a missing field', lambda u: u.pop('pinnedItems'))
    _expect_rejected('an empty calendar', lambda u: u['contributionsCollection']['contributionCalendar'].update(weeks=[]))
    _expect_rejected('a repo with no name', lambda u: u['pinnedItems']['nodes'][0].update(name='  '))

    user = _user()
    user['repositories']['nodes'][0]['languages']['edges'][0]['node']['color'] = 'red;background:url(//evil)'
    assert parse_user(user)['languages'][0]['color'] is None
    print('[OK]   drops a color that is not plain hex')

    user = _user()
    user['pinnedItems']['nodes'].insert(0, None)  # what GitHub sends for a pinned repo the token can't read
    assert [repo['name'] for repo in parse_user(user)['pinned']] == ['payday-bank']
    print('[OK]   skips an unreadable pinned repo')


def test_streaks():
    assert _streaks([]) == (0, 0)
    assert _streaks([1, 1, 0, 1, 1, 1]) == (3, 3)
    assert _streaks([1, 1, 0]) == (2, 2)      # today still empty: streak alive
    assert _streaks([1, 0, 0]) == (0, 1)      # yesterday empty too: streak over
    assert _streaks([0, 0, 0]) == (0, 0)
    print('[OK]   streaks')


def test_render():
    app = create_app()
    from app.routes.main.about import about_me
    from app.routes.main.index import home

    # Hostile snapshot inside a transaction that is rolled back, never committed.
    with app.test_request_context('/'):
        snapshot = db.session.get(SyncedSnapshot, 'github') or SyncedSnapshot(source='github')
        snapshot.data = parse_user(_user())
        db.session.add(snapshot)
        db.session.flush()
        try:
            for name, view in (('home', home), ('about', about_me)):
                html = view()
                assert 'class="gh-days"' in html, f'{name}: chart missing'
                assert 'grid-row-start: 5' in html, f'{name}: first partial week not offset'
                assert '<script>alert' not in html, f'{name}: description not escaped'
                print(f'[OK]   {name} renders the chart')
            assert 'payday-bank' in about_me() and '75.0%' in about_me()
            print('[OK]   about renders languages and pinned repos')
        finally:
            db.session.rollback()


if __name__ == '__main__':
    test_streaks()
    test_parse()
    test_render()
