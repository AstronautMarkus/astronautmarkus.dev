import re
from markupsafe import Markup
from flask import url_for


# ── Markdown renderer ─────────────────────────────────────────────────────────

def _esc(s: str) -> str:
    """HTML-escape a plain string."""
    return (
        s.replace('&', '&amp;')
         .replace('<', '&lt;')
         .replace('>', '&gt;')
         .replace('"', '&quot;')
    )


def _inline_markup(t: str) -> str:
    """Apply inline patterns to already-HTML-escaped text."""
    # Images: ![alt](url)
    t = re.sub(
        r'!\[([^\]]*)\]\(([^)\s]+)\)',
        lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}" style="max-width:100%;height:auto">',
        t,
    )
    # Links: [text](url)
    t = re.sub(
        r'\[([^\]]+)\]\(([^)\s]+)\)',
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener noreferrer">{m.group(1)}</a>',
        t,
    )
    # Bold ** and __
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'__(.+?)__',     r'<strong>\1</strong>', t)
    # Italic * and _ (word-boundary guard for _)
    t = re.sub(r'\*(.+?)\*',            r'<em>\1</em>', t)
    t = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<em>\1</em>', t)
    # Strikethrough
    t = re.sub(r'~~(.+?)~~', r'<del>\1</del>', t)
    return t


def _inline(text: str) -> str:
    """Process a line of markdown inline elements into HTML."""
    result = []
    last = 0
    for m in re.finditer(r'`([^`\n]+)`', text):
        raw = text[last:m.start()]
        if raw:
            result.append(_inline_markup(_esc(raw)))
        result.append(f'<code>{_esc(m.group(1))}</code>')
        last = m.end()
    tail = text[last:]
    if tail:
        result.append(_inline_markup(_esc(tail)))
    return ''.join(result)


def render_markdown(md: str) -> Markup:
    """Convert a markdown string to safe HTML (markupsafe.Markup)."""
    if not md:
        return Markup('')

    lines = md.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # ── Fenced code block (``` or ~~~) ───────────────────────
        fence = re.match(r'^(`{3,}|~{3,})([\w\-]*)', line)
        if fence:
            delim = fence.group(1)
            lang  = fence.group(2).strip()
            close = re.compile(r'^[' + re.escape(delim[0]) + r']{' + str(len(delim)) + r',}\s*$')
            code_lines: list[str] = []
            i += 1
            while i < n and not close.match(lines[i]):
                code_lines.append(_esc(lines[i]))
                i += 1
            i += 1  # skip closing fence
            lang_attr = f' class="language-{_esc(lang)}"' if lang else ''
            out.append(f'<pre><code{lang_attr}>' + '\n'.join(code_lines) + '</code></pre>')
            continue

        # ── Blank line ────────────────────────────────────────────
        if not stripped:
            i += 1
            continue

        # ── ATX heading ──────────────────────────────────────────
        h = re.match(r'^(#{1,6})\s+(.*)', line)
        if h:
            lvl = len(h.group(1))
            out.append(f'<h{lvl}>{_inline(h.group(2).strip())}</h{lvl}>')
            i += 1
            continue

        # ── Horizontal rule ──────────────────────────────────────
        if re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', stripped):
            out.append('<hr>')
            i += 1
            continue

        # ── Blockquote ───────────────────────────────────────────
        if stripped.startswith('>'):
            bq: list[str] = []
            while i < n and lines[i].strip().startswith('>'):
                bq.append(re.sub(r'^>\s?', '', lines[i]))
                i += 1
            out.append(f'<blockquote>{render_markdown(chr(10).join(bq))}</blockquote>')
            continue

        # ── Unordered list ───────────────────────────────────────
        if re.match(r'^[\*\-\+]\s', stripped):
            items: list[str] = []
            while i < n and re.match(r'^[\*\-\+]\s', lines[i].strip()):
                items.append(f'<li>{_inline(lines[i].strip()[2:].strip())}</li>')
                i += 1
            out.append('<ul>\n' + '\n'.join(items) + '\n</ul>')
            continue

        # ── Ordered list ─────────────────────────────────────────
        if re.match(r'^\d+\.\s', stripped):
            items = []
            while i < n and re.match(r'^\d+\.\s', lines[i].strip()):
                text = re.sub(r'^\d+\.\s+', '', lines[i].strip())
                items.append(f'<li>{_inline(text)}</li>')
                i += 1
            out.append('<ol>\n' + '\n'.join(items) + '\n</ol>')
            continue

        # ── Paragraph ────────────────────────────────────────────
        para: list[str] = []
        while i < n:
            l = lines[i]
            s = l.strip()
            if not s:
                break
            if (re.match(r'^#{1,6}\s', s)
                    or re.match(r'^`{3,}|^~{3,}', s)
                    or re.match(r'^[\*\-\+]\s', s)
                    or re.match(r'^\d+\.\s', s)
                    or re.match(r'^(\*{3,}|-{3,}|_{3,})\s*$', s)
                    or s.startswith('>')):
                break
            para.append(_inline(l))
            i += 1
        if para:
            out.append('<p>' + ' '.join(para) + '</p>')
        continue

    return Markup('\n'.join(out))


# ── Image shorthand expander ──────────────────────────────────────────────────

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
