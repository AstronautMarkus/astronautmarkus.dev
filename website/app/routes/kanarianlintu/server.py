from . import kanarianlintu_bp, log_hit
from flask import Response, render_template, url_for

# (name, is_dir, size, date, endpoint) — endpoint is None for fake resources
# routed through /fail?path=, or a real endpoint name for the ones with their
# own route (currently just .env).
ROOT_ENTRIES = [
    ('.env', False, '1.8K', '2026-05-11 10:02', 'kanarianlintu.env'),
    ('admin/', True, '-', '2026-05-11 10:02', None),
    ('backup/', True, '-', '2026-07-01 03:00', None),
    ('config/', True, '-', '2026-05-11 10:02', None),
    ('css/', True, '-', '2026-06-20 11:03', None),
    ('images/', True, '-', '2026-05-02 14:22', None),
    ('includes/', True, '-', '2026-05-11 10:02', None),
    ('index.php', False, '3.1K', '2026-05-11 10:02', None),
    ('info.php', False, '26', '2026-05-11 10:02', None),
    ('js/', True, '-', '2026-06-20 11:03', None),
    ('login.php', False, '3.4K', '2026-05-11 10:02', None),
    ('logs/', True, '-', '2026-08-05 23:59', None),
    ('phpinfo.php', False, '26', '2026-05-11 10:02', None),
    ('readme.txt', False, '512', '2026-05-11 10:02', None),
    ('robots.txt', False, '128', '2026-05-11 10:02', None),
    ('tmp/', True, '-', '2026-08-05 23:41', None),
    ('uploads/', True, '-', '2026-07-30 16:20', None),
]


@kanarianlintu_bp.route('/server')
def server():
    log_hit('index')
    entries = [
        {
            'name': name,
            'href': url_for(endpoint) if endpoint else url_for('kanarianlintu.fail', path=name),
            'is_dir': is_dir,
            'size': size,
            'date': date,
        }
        for name, is_dir, size, date, endpoint in ROOT_ENTRIES
    ]
    html = render_template(
        'kanarianlintu/apache_index.html',
        dir_path='/',
        parent_href=None,
        entries=entries,
    )
    return Response(html, mimetype='text/html')
