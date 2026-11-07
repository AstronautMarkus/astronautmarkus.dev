import re

from flask import Response, abort, render_template, request, url_for

from . import decoy_content as content
from . import log_hit

# Paths mass-scanned by bots/vulnerability crawlers within minutes of any host
# going public. Each one gets logged like a real hit; most also get realistic
# bait content (leaked "source", directory listings, config/secret files) via
# resolve_decoy() below so the whole thing holds up as a misconfigured Apache
# that's serving raw PHP source and has directory indexing left on everywhere.
DECOY_PATHS = [
    # WordPress
    '/wp-admin', '/wp-admin/', '/wp-login.php', '/wp-content/', '/wp-content',
    '/wp-includes/', '/wp-includes', '/wp-config.php', '/wp-config.php.bak',
    '/wp-json/wp/v2/users', '/xmlrpc.php',

    # Generic PHP admin panels / CMS
    '/admin.php', '/administrator', '/administrator/', '/phpmyadmin', '/phpMyAdmin',
    '/pma', '/adminer.php', '/login.php', '/config.php', '/install.php', '/setup.php',

    # Version control leaks
    '/.git/config', '/.git/HEAD', '/.svn/entries', '/.hg/',

    # Secrets / credentials (root .env handled separately with fake bait content)
    '/.env.bak', '/.env.local', '/.env.production', '/vendor/.env',
    '/.aws/credentials', '/credentials.json', '/secrets.yml', '/.npmrc',
    '/id_rsa', '/.ssh/id_rsa',

    # Backups / dumps
    '/backup.sql', '/backup.zip', '/dump.sql', '/db.sql', '/database.sql',

    # Framework / server introspection
    '/server-status', '/actuator/env', '/actuator/health', '/debug/pprof',
    '/telescope/requests', '/_profiler',

    # Misc
    '/shell.php', '/cmd.php', '/.htaccess', '/web.config', '/docker-compose.yml',
]


def resolve_decoy(url_path: str):
    """Return a Flask Response for a decoy path/resource, or None to fall back to a generic 404.

    url_path is a path-like string such as '/wp-admin/', 'debug.log', or
    'wp-admin/admin-ajax.php' — used both for directly-registered routes
    (leading slash) and for resource names logged via /fail?path=.
    """
    key = url_path.strip('/')
    basename = key.rsplit('/', 1)[-1]

    dir_key = key if key.endswith('/') else key + '/'
    if dir_key in content.DIRECTORY_LISTINGS:
        return _render_index(dir_key)

    if key in content.NAMED_TEXT:
        mimetype, body = content.NAMED_TEXT[key]
        return Response(body, mimetype=mimetype)
    if basename in content.NAMED_TEXT:
        mimetype, body = content.NAMED_TEXT[basename]
        return Response(body, mimetype=mimetype)

    if key in content.ENV_LIKE_NAMES:
        return Response(render_template('kanarianlintu/env.txt'), mimetype='text/plain')

    if key in content.SHELL_NAMES or basename in content.SHELL_NAMES:
        return _render_shell(url_path)

    return None


def _render_index(dir_key: str):
    entries = [
        {
            'name': name + ('/' if is_dir else ''),
            'href': url_for('kanarianlintu.fail', path=f'{dir_key}{name}' + ('/' if is_dir else '')),
            'is_dir': is_dir,
            'size': size,
            'date': date,
        }
        for name, is_dir, size, date in content.DIRECTORY_LISTINGS[dir_key]
    ]
    html = render_template(
        'kanarianlintu/apache_index.html',
        dir_path='/' + dir_key,
        parent_href=url_for('kanarianlintu.server'),
        entries=entries,
    )
    return Response(html, mimetype='text/html')


def _render_shell(url_path: str):
    output = content.SHELL_OUTPUT if request.method == 'POST' else None
    html = render_template('kanarianlintu/shell.html', path=url_path, output=output)
    return Response(html, mimetype='text/html')


def _endpoint_name(path: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', path).strip('_').lower()
    return f'kanarianlintu_decoy_{slug or "root"}'


def _decoy_view():
    log_hit(request.path)
    response = resolve_decoy(request.path)
    if response is not None:
        return response
    abort(404, description="Not Found")


def register_decoy_routes(app) -> None:
    """Register scanner-bait paths directly on the app, skipping any the real app already owns.

    Runs after every other blueprint is registered so app.url_map already reflects
    the real routes — the honeypot must never shadow genuine app functionality.
    """
    existing = {rule.rule for rule in app.url_map.iter_rules()}
    for path in DECOY_PATHS:
        if path in existing:
            continue
        app.add_url_rule(
            path,
            endpoint=_endpoint_name(path),
            view_func=_decoy_view,
            methods=['GET', 'POST'],
        )
