from flask import current_app
from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

REQUEST_TIMEOUT_MS = 20_000
MAX_CONTENT_CHARS = 12_000  # a blog post rarely needs more context than this to summarize well
MAX_TAGS = 8

SYSTEM_INSTRUCTION = (
    'You are an editorial assistant for a personal tech blog. Given a post title and, optionally, '
    'its Markdown content, suggest a rich excerpt and relevant tags. The excerpt should be a full, '
    'well-developed paragraph (roughly 3-5 sentences) that gives readers a genuine sense of what the '
    'post covers — go beyond a one-line teaser, but stay grounded in the actual content, never inventing '
    'details that are not supported by the title or the provided Markdown. Write naturally, avoid '
    "clickbait. Tags must be lowercase, concise, and free of hashtags or surrounding punctuation."
)


class AIServiceError(Exception):
    """Raised when an AI suggestion could not be generated."""


class BlogDescriptionSuggestion(BaseModel):
    description: str = Field(description='A full, well-developed excerpt (roughly 3-5 sentences) summarizing the post.')


class BlogMetadataSuggestion(BaseModel):
    description: str = Field(description='A full, well-developed excerpt (roughly 3-5 sentences) summarizing the post.')
    tags: list[str] = Field(description='5 to 8 short, lowercase tags for the post.')


def is_enabled() -> bool:
    cfg = current_app.config
    return bool(cfg.get('AI_FEATURES_ENABLED')) and bool(cfg.get('GEMINI_API_KEY'))


def _client() -> genai.Client:
    return genai.Client(
        api_key=current_app.config['GEMINI_API_KEY'],
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
    )


def suggest_blog_metadata(
    title: str,
    markdown_content: str = '',
    language: str = 'en',
    existing_tags: list[str] | None = None,
    include_tags: bool = True,
) -> dict:
    """Ask Gemini for an excerpt (and, optionally, tag suggestions) for a blog post draft.

    Tags are shared across languages (BlogTag has no per-language name), so callers regenerating
    the Spanish excerpt of an already-tagged post should pass include_tags=False.
    """
    if not is_enabled():
        raise AIServiceError('AI suggestions are not configured — set GEMINI_API_KEY to enable this feature.')

    title = title.strip()
    if not title:
        raise AIServiceError('A title is required to generate suggestions.')

    content = (markdown_content or '').strip()[:MAX_CONTENT_CHARS]
    lang_name = 'Spanish' if language == 'es' else 'English'

    prompt_parts = [f'Blog post title: {title}']
    if include_tags:
        prompt_parts.append(f'Write the excerpt and tags in {lang_name}.')
    else:
        prompt_parts.append(f'Write the excerpt in {lang_name}. Do not return tags.')
    if content:
        prompt_parts.append(f'Post content (Markdown):\n{content}')
    else:
        prompt_parts.append('No post content was provided yet — base the suggestion on the title alone.')
    if include_tags and existing_tags:
        tag_hint = ', '.join(sorted(existing_tags)[:40])
        prompt_parts.append(
            f'Tags already used on this blog — reuse one of these instead of inventing a near-duplicate '
            f'when it genuinely fits: {tag_hint}'
        )

    schema = BlogMetadataSuggestion if include_tags else BlogDescriptionSuggestion

    client = _client()
    try:
        response = client.models.generate_content(
            model=current_app.config.get('GEMINI_MODEL', 'gemini-3.6-flash'),
            contents='\n\n'.join(prompt_parts),
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type='application/json',
                response_schema=schema,
                temperature=0.4,
            ),
        )
    except errors.APIError as exc:
        raise AIServiceError(f'Gemini request failed: {exc.message}') from exc
    except Exception as exc:
        raise AIServiceError('Gemini request failed — check your connection and try again.') from exc

    result = response.parsed
    if result is None:
        raise AIServiceError('Gemini returned an unexpected response — try again.')

    if not include_tags:
        return {'description': result.description.strip()}

    tags = []
    seen = set()
    for tag in result.tags:
        name = tag.strip().lower().lstrip('#').strip()
        if name and name not in seen:
            seen.add(name)
            tags.append(name)

    return {'description': result.description.strip(), 'tags': tags[:MAX_TAGS]}
