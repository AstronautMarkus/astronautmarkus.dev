import io
import subprocess
import tempfile
from pathlib import Path

from ruamel.yaml import YAML

RENDERCV_TIMEOUT_SECONDS = 25
MAX_CV_YAML_BYTES = 2 * 1024 * 1024  # 2 MB

LOCALE_MAP = {'en': 'english', 'es': 'spanish'}

AVAILABLE_THEMES = ['classic', 'ember', 'engineeringclassic', 'engineeringresumes',
                     'harvard', 'ink', 'moderncv', 'opal', 'sb2nov']
# Source of truth: rendercv/schema/models/design/built_in_design.py:available_themes
# — recheck this list when upgrading the `rendercv` package.

SOCIAL_NETWORKS = ['LinkedIn', 'GitHub', 'GitLab', 'IMDB', 'Instagram', 'ORCID', 'Mastodon',
                    'StackOverflow', 'ResearchGate', 'YouTube', 'Google Scholar', 'Telegram',
                    'WhatsApp', 'Leetcode', 'X', 'Bluesky', 'Reddit']
# Source of truth: rendercv/schema/models/cv/social_network.py:SocialNetworkName
# — recheck this list when upgrading the `rendercv` package.

LIST_FIELDS = {'highlights', 'authors'}

BUILDER_ENTRY_TYPES = {
    'education': {
        'required': ['institution', 'area'],
        'fields': ['institution', 'area', 'degree', 'date', 'start_date', 'end_date',
                   'location', 'summary', 'highlights'],
    },
    'experience': {
        'required': ['company', 'position'],
        'fields': ['company', 'position', 'date', 'start_date', 'end_date',
                   'location', 'summary', 'highlights'],
    },
    'normal': {
        'required': ['name'],
        'fields': ['name', 'date', 'start_date', 'end_date', 'location', 'summary', 'highlights'],
    },
    'one_line': {
        'required': ['label', 'details'],
        'fields': ['label', 'details'],
    },
    'publication': {
        'required': ['title', 'authors'],
        'fields': ['title', 'authors', 'summary', 'doi', 'url', 'journal', 'date'],
    },
    'bullet': {
        'required': ['bullet'],
        'fields': ['bullet'],
    },
    'numbered': {
        'required': ['number'],
        'fields': ['number'],
    },
    'reversed_numbered': {
        'required': ['reversed_number'],
        'fields': ['reversed_number'],
    },
    # 'text' is handled specially in build_yaml_from_builder_data — it's not an
    # object type, a section using it is just a bare list of strings.
}


class RenderCVError(Exception):
    """Raised when rendercv fails to produce a PDF from the given YAML."""


def render_yaml_to_pdf(yaml_text: str) -> bytes:
    if not yaml_text or not yaml_text.strip():
        raise RenderCVError('The YAML content is empty.')

    encoded = yaml_text.encode('utf-8')
    if len(encoded) > MAX_CV_YAML_BYTES:
        raise RenderCVError(
            f'YAML is too large ({len(encoded)} bytes) — max {MAX_CV_YAML_BYTES} bytes.'
        )

    with tempfile.TemporaryDirectory(prefix='rendercv_') as tmp:
        tmp_path = Path(tmp)
        yaml_path = tmp_path / 'cv.yaml'
        yaml_path.write_bytes(encoded)
        pdf_path = tmp_path / 'cv.pdf'

        cmd = [
            'rendercv', 'render', str(yaml_path),
            '--pdf-path', str(pdf_path),
            '--dont-generate-markdown',  # implicitly disables HTML too
            '--dont-generate-png',
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=RENDERCV_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise RenderCVError(
                f'rendercv exceeded the {RENDERCV_TIMEOUT_SECONDS}s timeout.'
            ) from exc
        except FileNotFoundError as exc:
            raise RenderCVError(
                'The "rendercv" command is not installed. Run: pip install "rendercv[full]"'
            ) from exc

        if result.returncode != 0 or not pdf_path.exists():
            message = (result.stdout or result.stderr or 'Unknown rendercv error.').strip()
            raise RenderCVError(message)

        return pdf_path.read_bytes()


def _split_lines(text) -> list[str]:
    """Split a textarea's raw text into one item per non-blank line."""
    if not isinstance(text, str):
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


def build_yaml_from_builder_data(data: dict, language: str) -> tuple[str, list[str]]:
    """Map the CV builder's structured JSON into RenderCV-shaped YAML text.

    Returns (yaml_text, warnings) — warnings name any section/entry dropped for
    missing required fields. Never raises on malformed *content*; a non-dict
    `data` is treated as empty. The caller is responsible for treating a blank
    `cv.name` as a hard validation error before calling this.
    """
    warnings: list[str] = []
    if not isinstance(data, dict):
        data = {}

    header = data.get('header') or {}
    cv: dict = {}
    for key in ('name', 'headline', 'location', 'email', 'phone', 'website'):
        val = header.get(key)
        if isinstance(val, str) and val.strip():
            cv[key] = val.strip()

    social_networks = []
    for sn in data.get('social_networks') or []:
        network = (sn.get('network') or '').strip()
        username = (sn.get('username') or '').strip()
        if network and username:
            social_networks.append({'network': network, 'username': username})
        elif network or username:
            warnings.append(f'Skipped an incomplete social network entry ({network or username}).')
    if social_networks:
        cv['social_networks'] = social_networks

    sections: dict = {}
    for sec in data.get('sections') or []:
        title = (sec.get('title') or '').strip()
        entry_type = sec.get('entry_type') or ''
        if not title:
            warnings.append('Skipped a section with no title.')
            continue

        if entry_type == 'text':
            paragraphs = _split_lines(sec.get('text'))
            if paragraphs:
                sections[title] = paragraphs
            else:
                warnings.append(f'Skipped section "{title}" — no content.')
            continue

        type_def = BUILDER_ENTRY_TYPES.get(entry_type)
        if not type_def:
            warnings.append(f'Skipped section "{title}" — unrecognized entry type.')
            continue

        built_entries = []
        for entry in sec.get('entries') or []:
            fields = entry.get('fields') or {}
            missing = [f for f in type_def['required'] if not (fields.get(f) or '').strip()]
            if missing:
                warnings.append(f'Skipped an entry in "{title}" — missing {", ".join(missing)}.')
                continue
            built = {}
            for f in type_def['fields']:
                raw = fields.get(f)
                if f in LIST_FIELDS:
                    items = _split_lines(raw)
                    if items:
                        built[f] = items
                elif isinstance(raw, str) and raw.strip():
                    built[f] = raw.strip()
            built_entries.append(built)

        if built_entries:
            sections[title] = built_entries
        else:
            warnings.append(f'Skipped section "{title}" — no valid entries.')

    if sections:
        cv['sections'] = sections

    root: dict = {}
    if cv:
        root['cv'] = cv
    theme = (data.get('design') or {}).get('theme')
    if theme in AVAILABLE_THEMES:
        root['design'] = {'theme': theme}
    locale_name = LOCALE_MAP.get(language)
    if locale_name:
        root['locale'] = {'language': locale_name}

    stream = io.StringIO()
    yaml = YAML()
    yaml.default_flow_style = False
    yaml.dump(root, stream)
    return stream.getvalue(), warnings
