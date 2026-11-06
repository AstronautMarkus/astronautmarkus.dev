import re
from collections import Counter
from datetime import date, datetime

import requests
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.models.models import SyncedSnapshot

GRAPHQL_URL = 'https://api.github.com/graphql'
REQUEST_TIMEOUT = 20
TOP_LANGUAGES = 6

# One query for everything the site shows. The token needs no scopes: it only reads public data.
# shortcut: only the first 100 public repos count toward languages; paginate if that ever stops covering them all.
QUERY = '''
query($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } } }
    }
    pinnedItems(first: 6, types: REPOSITORY) {
      nodes { ... on Repository { name description url stargazerCount primaryLanguage { name color } } }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}
'''

LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}
_HEX_COLOR = re.compile(r'#[0-9a-fA-F]{6}')


class GithubSyncError(Exception):
    """Raised when GitHub could not be reached or answered with something we won't store."""


# ── Validation: everything below ends up in templates, some of it inside style/href attributes ──

def _count(value) -> int:
    if type(value) is not int or value < 0:  # `type is` rejects bools, which are ints too
        raise ValueError(f'expected a non-negative integer, got {value!r}')
    return value


def _text(value, limit: int, required: bool = False) -> str:
    if value is None and not required:
        return ''
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f'expected text, got {value!r}')
    return value.strip()[:limit]


def _color(value) -> str | None:
    # Rendered inside style="": anything but a plain hex color is dropped, not trusted.
    return value if isinstance(value, str) and _HEX_COLOR.fullmatch(value) else None


def _repo_url(value) -> str:
    if not isinstance(value, str) or not value.startswith('https://github.com/'):
        raise ValueError(f'unexpected repository URL {value!r}')
    return value


def _streaks(counts: list[int]) -> tuple[int, int]:
    """(current, longest) runs of days with contributions. An empty today doesn't break the streak yet."""
    longest = run = 0
    for count in counts:
        run = run + 1 if count else 0
        longest = max(longest, run)

    current = 0
    days = counts[:-1] if counts and not counts[-1] else counts
    for count in reversed(days):
        if not count:
            break
        current += 1
    return current, longest


def parse_user(user) -> dict:
    """Turn the GraphQL `user` object into the snapshot the templates read. Raises GithubSyncError on any surprise."""
    try:
        contributions = user['contributionsCollection']
        calendar = contributions['contributionCalendar']

        weeks = []
        for week in calendar['weeks']:
            days = [
                [date.fromisoformat(day['date']).isoformat(), _count(day['contributionCount']), LEVELS[day['contributionLevel']]]
                for day in week['contributionDays']
            ]
            if not 1 <= len(days) <= 7:
                raise ValueError(f'a week with {len(days)} days')
            weeks.append(days)
        if not weeks:
            raise ValueError('empty contribution calendar')
        current_streak, longest_streak = _streaks([day[1] for week in weeks for day in week])

        sizes, colors = Counter(), {}
        for repo in user['repositories']['nodes']:
            for edge in repo['languages']['edges']:
                name = _text(edge['node']['name'], 50, required=True)
                sizes[name] += _count(edge['size'])
                colors[name] = _color(edge['node']['color'])
        total_size = sum(sizes.values())
        languages = [
            {'name': name, 'color': colors[name], 'pct': round(size * 100 / total_size, 1)}
            for name, size in sizes.most_common(TOP_LANGUAGES)
        ]

        pinned = []
        for repo in user['pinnedItems']['nodes']:
            if repo is None:  # not readable with this token, see fetch_user
                continue
            language = repo['primaryLanguage'] or {}
            pinned.append({
                'name': _text(repo['name'], 100, required=True),
                'description': _text(repo['description'], 300),
                'url': _repo_url(repo['url']),
                'stars': _count(repo['stargazerCount']),
                'language': _text(language.get('name'), 50),
                'color': _color(language.get('color')),
            })

        return {
            'public_repos': _count(user['repositories']['totalCount']),
            'contributions': _count(calendar['totalContributions']),
            'commits': _count(contributions['totalCommitContributions']),
            'pull_requests': _count(contributions['totalPullRequestContributions']),
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'weeks': weeks,
            'languages': languages,
            'pinned': pinned,
        }
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise GithubSyncError(f'Unexpected GitHub response: {exc!r}') from exc


def fetch_user(login: str, token: str) -> dict:
    """Run the GraphQL query and return the raw `user` object."""
    try:
        response = requests.post(
            GRAPHQL_URL,
            json={'query': QUERY, 'variables': {'login': login}},
            headers={'Authorization': f'Bearer {token}', 'User-Agent': 'astronautmarkus.dev github-sync'},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise GithubSyncError(f'Could not reach GitHub: {exc}') from exc

    if not isinstance(payload, dict):
        raise GithubSyncError('GitHub answered with something other than a JSON object')
    # A pinned repo the token may not read (e.g. an org that blocks long-lived tokens) comes back as null
    # plus an error: drop that repo, keep the sync. Any other error is fatal.
    errors = [
        error for error in payload.get('errors') or []
        if not (isinstance(error, dict) and (error.get('path') or [])[:2] == ['user', 'pinnedItems'])
    ]
    if errors:
        messages = '; '.join(str(error.get('message', error)) for error in errors if isinstance(error, dict))
        raise GithubSyncError(f'GitHub GraphQL error: {messages or errors!r}')
    user = (payload.get('data') or {}).get('user')
    if not isinstance(user, dict):
        raise GithubSyncError(f'GitHub user {login!r} not found')
    return user


def sync_github() -> dict:
    """Fetch, validate and store the GitHub snapshot. A failed run keeps the last good snapshot."""
    login = current_app.config['GITHUB_USERNAME']
    token = current_app.config['GITHUB_TOKEN']
    if not (login and token):
        raise GithubSyncError('GITHUB_USERNAME and GITHUB_TOKEN must be configured')

    data = parse_user(fetch_user(login, token))
    snapshot = db.session.get(SyncedSnapshot, 'github') or SyncedSnapshot(source='github')
    snapshot.data = data
    snapshot.synced_at = datetime.utcnow()
    db.session.add(snapshot)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        raise GithubSyncError(f'Could not save the GitHub snapshot: {exc}') from exc

    return {'contributions': data['contributions'], 'repos': data['public_repos'], 'pinned': len(data['pinned'])}
