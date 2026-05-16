import re
from flask import url_for


def expand_post_images(text: str, post_slug: str) -> str:
    """
    Replace ``@filename.ext`` shorthands in markdown with full /media/ URLs.

    The raw markdown is stored as-is with the @ prefix. At serve time this
    function rewrites every occurrence so the browser sees real URLs.

    Pattern matched:  @<filename>.<extension>
    Expands to:       /media/blog/posts/<post-slug>/images/<filename>.<extension>

    Example in the .md file:
        ![DNS Flow diagram](@dns-flow.png)
        ![Server setup](@server-setup.jpg)

    Becomes at render time:
        ![DNS Flow diagram](/media/blog/posts/how-dns-works/images/dns-flow.png)
        ![Server setup](/media/blog/posts/how-dns-works/images/server-setup.jpg)
    """
    def _replace(m: re.Match) -> str:
        filename = m.group(1)
        path = f'blog/posts/{post_slug}/images/{filename}'
        return url_for('serve_media', file_path=path)

    # Match @word[word/-/.]*.ext — must start with word char, must have extension
    return re.sub(r'@([\w][\w\.\-]*\.\w+)', _replace, text)
