from io import BytesIO
from pathlib import Path

from flask import Response
from PIL import Image

from app.models.models import Visit
from . import utils_bp


def _format_visitor_counter(total_visits: int) -> str:
    if total_visits <= 9999:
        return f"{total_visits:04d}"
    return str(total_visits)


def _build_counter_gif(counter_text: str) -> bytes:
    base_dir = Path(__file__).resolve().parents[2]
    digits_dir = base_dir / 'static' / 'img' / 'booru-jaypee'

    digit_images = [Image.open(digits_dir / f'{digit}.gif') for digit in counter_text]
    frame_counts = [getattr(image, 'n_frames', 1) for image in digit_images]
    total_frames = max(frame_counts)

    frames = []
    durations = []

    total_width = sum(image.size[0] for image in digit_images)
    max_height = max(image.size[1] for image in digit_images)

    try:
        for frame_index in range(total_frames):
            composed = Image.new('RGBA', (total_width, max_height), (0, 0, 0, 0))
            duration = 100
            x_offset = 0

            for image in digit_images:
                image.seek(frame_index % getattr(image, 'n_frames', 1))
                current_frame = image.convert('RGBA')
                composed.paste(current_frame, (x_offset, 0), current_frame)
                x_offset += image.size[0]
                duration = min(duration, image.info.get('duration', 100))

            frames.append(composed)
            durations.append(duration)
    finally:
        for image in digit_images:
            image.close()

    output = BytesIO()
    frames[0].save(
        output,
        format='GIF',
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        transparency=0,
        disposal=2,
    )

    return output.getvalue()


@utils_bp.route('/visitor-counter')
def visitor_counter() -> Response:
    total_visits = Visit.query.count()
    counter_text = _format_visitor_counter(total_visits)
    gif_bytes = _build_counter_gif(counter_text)

    response = Response(gif_bytes, mimetype='image/gif')
    response.headers['Cache-Control'] = 'no-store, max-age=0'
    return response