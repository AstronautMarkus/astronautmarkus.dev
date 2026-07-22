import subprocess
import tempfile
from pathlib import Path

RENDERCV_TIMEOUT_SECONDS = 25
MAX_CV_YAML_BYTES = 2 * 1024 * 1024  # 2 MB


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
