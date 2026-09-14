from flask import g, current_app, render_template
from jinja2 import TemplateNotFound

SUPPORTED_LANGUAGES = ('en', 'es')
LANG_COOKIE_NAME    = 'lang'
DEFAULT_LANGUAGE    = 'en'


def get_current_language():
    """Return the active language for the current request, falling back to the default."""
    lang = getattr(g, 'current_lang', None)
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def localized_template_name(template_name: str) -> str:
    """
    Given a template path, return the localized variant if it exists.

    Examples (lang = 'es'):
        'home.html'              -> 'home_es.html'        (if it exists)
        'emails/contact.html'    -> 'emails/contact_es.html'  (if it exists)
        'home.html'              -> 'home.html'           (fallback when _es missing)
    """
    lang = get_current_language()

    if lang == DEFAULT_LANGUAGE:
        return template_name

    dot = template_name.rfind('.')
    candidate = (
        f'{template_name}_{lang}'
        if dot == -1
        else f'{template_name[:dot]}_{lang}{template_name[dot:]}'
    )

    try:
        current_app.jinja_loader.get_source(current_app.jinja_env, candidate)
        return candidate
    except TemplateNotFound:
        return template_name


def render_localized_template(template_name: str, **context):
    """Drop-in replacement for render_template that auto-selects the localized variant."""
    return render_template(localized_template_name(template_name), **context)


# ── Admin dashboard UI strings ──────────────────────────────────────────
#
# The public site localizes by duplicating whole templates (see
# `localized_template_name` above) because its pages are long-form prose
# that genuinely differs per language. The admin dashboard is the opposite
# case — ~24 templates of short, heavily-repeated UI chrome (buttons,
# table headers, flash messages) — so duplicating files would mean keeping
# two copies of every table row in sync forever. Instead each template
# stays a single file and pulls short strings from this dict via `t()`,
# the same style already used for date formatting in `_dtfmt` and for
# `age_geek` in `main/profile.py`.
ADMIN_STRINGS = {
    # ── Common / shared across many pages ──
    'common.actions': {'en': 'Actions', 'es': 'Acciones'},
    'common.edit': {'en': 'Edit', 'es': 'Editar'},
    'common.delete': {'en': 'Delete', 'es': 'Eliminar'},
    'common.delete_selected': {'en': 'Delete selected', 'es': 'Eliminar seleccionados'},
    'common.selected': {'en': 'selected', 'es': 'seleccionados'},
    'common.save_changes': {'en': 'Save Changes', 'es': 'Guardar cambios'},
    'common.cancel': {'en': 'Cancel', 'es': 'Cancelar'},
    'common.back_to_list': {'en': '← Back to list', 'es': '← Volver al listado'},
    'common.created': {'en': 'Created', 'es': 'Creado'},
    'common.date': {'en': 'Date', 'es': 'Fecha'},
    'common.title': {'en': 'Title', 'es': 'Título'},
    'common.name': {'en': 'Name', 'es': 'Nombre'},
    'common.status': {'en': 'Status', 'es': 'Estado'},
    'common.language': {'en': 'Language', 'es': 'Idioma'},
    'common.languages': {'en': 'Languages', 'es': 'Idiomas'},
    'common.search': {'en': 'Search', 'es': 'Buscar'},
    'common.filter': {'en': 'Filter', 'es': 'Filtrar'},
    'common.clear': {'en': 'Clear', 'es': 'Limpiar'},
    'common.clear_search': {'en': 'Clear search', 'es': 'Limpiar búsqueda'},
    'common.clear_filters': {'en': 'Clear filters', 'es': 'Limpiar filtros'},
    'common.view': {'en': 'View', 'es': 'Ver'},
    'common.download': {'en': 'Download', 'es': 'Descargar'},
    'common.select': {'en': 'Select', 'es': 'Seleccionar'},
    'common.optional': {'en': 'optional', 'es': 'opcional'},
    'common.upload_replace_hint': {'en': 'Upload a new file to replace it.', 'es': 'Sube un archivo nuevo para reemplazarlo.'},
    'common.current_file': {'en': 'Current file:', 'es': 'Archivo actual:'},

    # ── Base layout (topbar / sidebar) ──
    'base.toggle_menu': {'en': 'Toggle menu', 'es': 'Alternar menú'},
    'base.toggle_theme': {'en': 'Toggle theme', 'es': 'Alternar tema'},
    'base.signed_in_as': {'en': 'Signed in as', 'es': 'Sesión iniciada como'},
    'base.view_site': {'en': 'View Site', 'es': 'Ver sitio'},
    'base.logout': {'en': 'Logout', 'es': 'Cerrar sesión'},
    'base.switch_language': {'en': 'Switch language', 'es': 'Cambiar idioma'},
    'base.unread_message_one': {'en': '{n} unread message', 'es': '{n} mensaje sin leer'},
    'base.unread_message_other': {'en': '{n} unread messages', 'es': '{n} mensajes sin leer'},

    # ── Sidebar navigation ──
    'nav.main': {'en': 'Main', 'es': 'Principal'},
    'nav.content': {'en': 'Content', 'es': 'Contenido'},
    'nav.contact': {'en': 'Contact', 'es': 'Contacto'},
    'nav.system': {'en': 'System', 'es': 'Sistema'},
    'nav.dashboard': {'en': 'Dashboard', 'es': 'Panel'},
    'nav.visits': {'en': 'Visits', 'es': 'Visitas'},
    'nav.honeypot': {'en': 'Honeypot', 'es': 'Honeypot'},
    'nav.portfolio': {'en': 'Portfolio', 'es': 'Portafolio'},
    'nav.gallery': {'en': 'Gallery', 'es': 'Galería'},
    'nav.cv_files': {'en': 'CV Files', 'es': 'Archivos CV'},
    'nav.blog_posts': {'en': 'Blog Posts', 'es': 'Entradas del blog'},
    'nav.categories': {'en': 'Categories', 'es': 'Categorías'},
    'nav.proyectadas': {'en': 'Proyectadas', 'es': 'Proyectadas'},
    'nav.guestbook': {'en': 'Guestbook', 'es': 'Libro de visitas'},
    'nav.inbox': {'en': 'Inbox', 'es': 'Bandeja de entrada'},
    'nav.blocked_senders': {'en': 'Blocked Senders', 'es': 'Remitentes bloqueados'},
    'nav.backups': {'en': 'Backups', 'es': 'Copias de seguridad'},

    # ── Dashboard home ──
    'dashboard.overview': {'en': 'Overview', 'es': 'Resumen'},
    'dashboard.portfolio_projects': {'en': 'Portfolio Projects', 'es': 'Proyectos de portafolio'},
    'dashboard.total_visits': {'en': 'Total Visits', 'es': 'Visitas totales'},
    'dashboard.honeypot_hits': {'en': 'Honeypot Hits', 'es': 'Detecciones honeypot'},
    'dashboard.messages': {'en': 'Messages', 'es': 'Mensajes'},
    'dashboard.view_all': {'en': 'View all', 'es': 'Ver todos'},
    'dashboard.manage': {'en': 'Manage', 'es': 'Gestionar'},
    'dashboard.analytics': {'en': 'Analytics', 'es': 'Analítica'},
    'dashboard.view_log': {'en': 'View log', 'es': 'Ver registro'},
    'dashboard.unread': {'en': 'unread', 'es': 'sin leer'},
    'dashboard.all_read': {'en': 'all read', 'es': 'todo leído'},
    'dashboard.category_one': {'en': 'category', 'es': 'categoría'},
    'dashboard.category_other': {'en': 'categories', 'es': 'categorías'},
    'dashboard.recent_messages': {'en': 'Recent Messages', 'es': 'Mensajes recientes'},
    'dashboard.recent_posts': {'en': 'Recent Blog Posts', 'es': 'Entradas recientes'},
    'dashboard.recent_projects': {'en': 'Recent Projects', 'es': 'Proyectos recientes'},
    'dashboard.from': {'en': 'From', 'es': 'De'},
    'dashboard.subject': {'en': 'Subject', 'es': 'Asunto'},
    'dashboard.new_badge': {'en': 'new', 'es': 'nuevo'},
    'dashboard.live': {'en': 'Live', 'es': 'Publicado'},
    'dashboard.draft': {'en': 'Draft', 'es': 'Borrador'},
    'dashboard.no_messages': {'en': 'No messages yet.', 'es': 'Aún no hay mensajes.'},
    'dashboard.no_posts': {'en': 'No posts yet.', 'es': 'Aún no hay entradas.'},
    'dashboard.write_one': {'en': 'Write one →', 'es': 'Escribe una →'},
    'dashboard.no_projects': {'en': 'No projects yet.', 'es': 'Aún no hay proyectos.'},
    'dashboard.add_one': {'en': 'Add one →', 'es': 'Agrega uno →'},

    # ── Pagination / search bar (admin/_macros.html) ──
    'macros.showing': {'en': 'Showing', 'es': 'Mostrando'},
    'macros.of': {'en': 'of', 'es': 'de'},
    'macros.prev': {'en': '← Prev', 'es': '← Anterior'},
    'macros.next': {'en': 'Next →', 'es': 'Siguiente →'},
    'macros.search_placeholder': {'en': 'Search…', 'es': 'Buscar…'},

    # ── Blog categories & posts ──
    'blog.edit_category': {'en': 'Edit Category', 'es': 'Editar categoría'},
    'blog.new_category': {'en': 'New Category', 'es': 'Nueva categoría'},
    'blog.new_category_btn': {'en': '+ New Category', 'es': '+ Nueva categoría'},
    'blog.category_details': {'en': 'Category Details', 'es': 'Detalles de la categoría'},
    'blog.slug': {'en': 'Slug', 'es': 'Slug'},
    'blog.slug_locked_hint': {'en': 'Locked after creation to preserve future URLs.', 'es': 'Bloqueado tras la creación para preservar las URLs futuras.'},
    'blog.slug_blank_hint_name': {'en': 'Leave blank to auto-generate from the name.', 'es': 'Déjalo en blanco para generarlo automáticamente a partir del nombre.'},
    'blog.slug_blank_hint_title': {'en': 'Leave blank to auto-generate from the English title.', 'es': 'Déjalo en blanco para generarlo automáticamente a partir del título en inglés.'},
    'blog.enable_es_category': {'en': 'Enable Spanish name for this category', 'es': 'Habilitar nombre en español para esta categoría'},
    'blog.create_category': {'en': 'Create Category', 'es': 'Crear categoría'},
    'blog.categories_title': {'en': 'Blog Categories', 'es': 'Categorías del blog'},
    'blog.back_to_posts': {'en': '← Posts', 'es': '← Entradas'},
    'blog.posts_count': {'en': 'Posts', 'es': 'Entradas'},
    'blog.confirm_delete_category': {'en': 'Delete category «{name}»?', 'es': '¿Eliminar la categoría «{name}»?'},
    'blog.no_categories': {'en': 'No categories yet.', 'es': 'Aún no hay categorías.'},
    'blog.create_first': {'en': 'Create the first one →', 'es': 'Crea la primera →'},

    'blog.post_singular': {'en': 'Post', 'es': 'Entrada'},
    'blog.posts_title': {'en': 'Blog Posts', 'es': 'Entradas del blog'},
    'blog.categories_link': {'en': 'Categories', 'es': 'Categorías'},
    'blog.new_post_btn': {'en': '+ New Post', 'es': '+ Nueva entrada'},
    'blog.search_by_title': {'en': 'Search by title…', 'es': 'Buscar por título…'},
    'blog.cover': {'en': 'Cover', 'es': 'Portada'},
    'blog.category': {'en': 'Category', 'es': 'Categoría'},
    'blog.published_col': {'en': 'Published', 'es': 'Publicado'},
    'blog.views': {'en': 'Views', 'es': 'Vistas'},
    'blog.uncategorized': {'en': '— Uncategorized —', 'es': '— Sin categoría —'},
    'blog.click_to_unpublish': {'en': 'Click to unpublish', 'es': 'Clic para despublicar'},
    'blog.click_to_publish': {'en': 'Click to publish', 'es': 'Clic para publicar'},
    'blog.confirm_delete_post': {'en': 'Delete post «{title}»? This cannot be undone.', 'es': '¿Eliminar la entrada «{title}»? Esta acción no se puede deshacer.'},
    'blog.no_posts_match': {'en': 'No posts match "{q}".', 'es': 'Ninguna entrada coincide con "{q}".'},
    'blog.no_posts': {'en': 'No posts yet.', 'es': 'Aún no hay entradas.'},
    'blog.write_first': {'en': 'Write your first post →', 'es': 'Escribe tu primera entrada →'},

    'blog.edit_post': {'en': 'Edit Post', 'es': 'Editar entrada'},
    'blog.new_post': {'en': 'New Post', 'es': 'Nueva entrada'},
    'blog.post_content': {'en': 'Post Content', 'es': 'Contenido de la entrada'},
    'blog.excerpt': {'en': 'Excerpt / Short Description', 'es': 'Extracto / Descripción corta'},
    'blog.markdown_en': {'en': 'Markdown Content (EN)', 'es': 'Contenido Markdown (EN)'},
    'blog.markdown_es': {'en': 'Contenido Markdown (ES)', 'es': 'Contenido Markdown (ES)'},
    'blog.download_md_en': {'en': '↓ Download EN .md', 'es': '↓ Descargar .md (EN)'},
    'blog.download_md_es': {'en': '↓ Descargar ES .md', 'es': '↓ Descargar .md (ES)'},
    'blog.enable_es_post': {'en': 'Enable Spanish content for this post', 'es': 'Habilitar contenido en español para esta entrada'},
    'blog.create_post': {'en': 'Create Post', 'es': 'Crear entrada'},
    'blog.header_cover_image': {'en': 'Header / Cover Image', 'es': 'Imagen de cabecera / portada'},
    'blog.upload_replace_header': {'en': 'Upload a new file to replace the current header.', 'es': 'Sube un archivo nuevo para reemplazar la cabecera actual.'},
    'blog.new_cover_not_saved': {'en': 'New cover — not saved yet', 'es': 'Nueva portada — aún no guardada'},
    'blog.tags': {'en': 'Tags', 'es': 'Etiquetas'},
    'blog.tags_hint': {'en': 'Comma-separated list of tags.', 'es': 'Lista de etiquetas separadas por comas.'},
    'blog.publication_date': {'en': 'Publication Date', 'es': 'Fecha de publicación'},
    'blog.publication_date_hint': {'en': 'Defaults to current date/time on creation.', 'es': 'Por defecto usa la fecha/hora actual al crear.'},
    'blog.publish_checkbox': {'en': 'Publish this post (make it visible on the public site)', 'es': 'Publicar esta entrada (visible en el sitio público)'},
    'blog.post_images': {'en': 'Post Images', 'es': 'Imágenes de la entrada'},
    'blog.post_images_hint': {'en': 'Upload images, then copy their URLs to paste into your Markdown.', 'es': 'Sube imágenes y luego copia sus URLs para pegarlas en tu Markdown.'},
    'blog.copy_url': {'en': 'Copy URL', 'es': 'Copiar URL'},
    'blog.remove': {'en': 'Remove', 'es': 'Quitar'},
    'blog.no_images_yet': {'en': 'No images yet.', 'es': 'Aún no hay imágenes.'},
    'blog.click_to_upload': {'en': 'Click to upload or drag & drop', 'es': 'Haz clic para subir o arrastra y suelta'},

    # ── Contact ──
    'contact.inbox_title': {'en': 'Contact Inbox', 'es': 'Bandeja de contacto'},
    'contact.unread_n': {'en': '{n} unread', 'es': '{n} sin leer'},
    'contact.search_ph': {'en': 'Search name, email, subject…', 'es': 'Buscar nombre, email, asunto…'},
    'contact.subject': {'en': 'Subject', 'es': 'Asunto'},
    'contact.lang': {'en': 'Lang', 'es': 'Idioma'},
    'contact.received': {'en': 'Received', 'es': 'Recibido'},
    'contact.block_confirm': {'en': 'Block {email} and delete all their messages?', 'es': '¿Bloquear a {email} y eliminar todos sus mensajes?'},
    'contact.delete_message_confirm': {'en': 'Delete this message?', 'es': '¿Eliminar este mensaje?'},
    'contact.no_messages_match': {'en': 'No messages match "{q}".', 'es': 'Ningún mensaje coincide con "{q}".'},
    'contact.no_messages': {'en': 'No messages yet.', 'es': 'Aún no hay mensajes.'},
    'contact.message_hash': {'en': 'Message #{id}', 'es': 'Mensaje #{id}'},
    'contact.back_to_inbox': {'en': '← Back to inbox', 'es': '← Volver a la bandeja'},
    'contact.block_sender': {'en': 'Block sender', 'es': 'Bloquear remitente'},
    'contact.email': {'en': 'Email', 'es': 'Correo'},
    'contact.received_at': {'en': 'Received', 'es': 'Recibido'},
    'contact.message': {'en': 'Message', 'es': 'Mensaje'},
    'contact.blocked_senders_title': {'en': 'Blocked Senders', 'es': 'Remitentes bloqueados'},
    'contact.block_manual_title': {'en': 'Block an email or IP manually', 'es': 'Bloquear un correo o IP manualmente'},
    'contact.ip_address': {'en': 'IP address', 'es': 'Dirección IP'},
    'contact.block': {'en': 'Block', 'es': 'Bloquear'},
    'contact.reason': {'en': 'Reason', 'es': 'Motivo'},
    'contact.blocked_col': {'en': 'Blocked', 'es': 'Bloqueado'},
    'contact.auto_rate_limit': {'en': 'Auto (rate limit)', 'es': 'Automático (límite de tasa)'},
    'contact.manual': {'en': 'Manual', 'es': 'Manual'},
    'contact.unblock_confirm': {'en': 'Unblock this sender?', 'es': '¿Desbloquear a este remitente?'},
    'contact.unblock': {'en': 'Unblock', 'es': 'Desbloquear'},
    'contact.no_blocked': {'en': 'No blocked senders yet.', 'es': 'Aún no hay remitentes bloqueados.'},

    # ── CV files ──
    'cv.files_title': {'en': 'CV Files', 'es': 'Archivos CV'},
    'cv.upload_btn': {'en': '+ Upload CV', 'es': '+ Subir CV'},
    'cv.source': {'en': 'Source', 'es': 'Origen'},
    'cv.file_path': {'en': 'File Path', 'es': 'Ruta del archivo'},
    'cv.uploaded': {'en': 'Uploaded', 'es': 'Subido'},
    'cv.generated': {'en': 'Generated', 'es': 'Generado'},
    'cv.uploaded_src': {'en': 'Uploaded', 'es': 'Subido'},
    'cv.yaml': {'en': 'YAML', 'es': 'YAML'},
    'cv.confirm_delete': {'en': 'Delete CV ({lang})? This cannot be undone.', 'es': '¿Eliminar CV ({lang})? Esta acción no se puede deshacer.'},
    'cv.no_files': {'en': 'No CV files yet.', 'es': 'Aún no hay archivos CV.'},
    'cv.upload_first': {'en': 'Upload your first CV →', 'es': 'Sube tu primer CV →'},
    'cv.edit_title': {'en': 'Edit CV', 'es': 'Editar CV'},
    'cv.upload_title': {'en': 'Upload CV', 'es': 'Subir CV'},
    'cv.details': {'en': 'CV Details', 'es': 'Detalles del CV'},
    'cv.select_placeholder': {'en': '— select —', 'es': '— seleccionar —'},
    'cv.lang_hint': {'en': 'Each language identifies a distinct CV version.', 'es': 'Cada idioma identifica una versión distinta del CV.'},
    'cv.tab_upload': {'en': 'Upload PDF', 'es': 'Subir PDF'},
    'cv.tab_generate': {'en': 'Generate from YAML', 'es': 'Generar desde YAML'},
    'cv.tab_builder': {'en': 'Build from Scratch', 'es': 'Crear desde cero'},
    'cv.pdf_file': {'en': 'PDF File', 'es': 'Archivo PDF'},
    'cv.view_current_file': {'en': 'View current file ↗', 'es': 'Ver archivo actual ↗'},
    'cv.pdf_hint': {'en': 'PDF only — max 10 MB', 'es': 'Solo PDF — máx. 10 MB'},
    'cv.view_current_yaml': {'en': 'View current YAML ↗', 'es': 'Ver YAML actual ↗'},
    'cv.regenerate_hint': {'en': 'The PDF is regenerated whenever the YAML below changes.', 'es': 'El PDF se regenera cada vez que cambia el YAML de abajo.'},
    'cv.yaml_field': {'en': 'RenderCV YAML', 'es': 'YAML de RenderCV'},
    'cv.yaml_hint': {'en': 'Or upload a .yaml/.yml file below — max 2 MB. Leave both empty to keep the current version.', 'es': 'O sube un archivo .yaml/.yml abajo — máx. 2 MB. Deja ambos vacíos para conservar la versión actual.'},
    'cv.builder_header': {'en': 'Header', 'es': 'Encabezado'},
    'cv.builder_name': {'en': 'Name', 'es': 'Nombre'},
    'cv.builder_headline': {'en': 'Headline', 'es': 'Titular'},
    'cv.builder_location': {'en': 'Location', 'es': 'Ubicación'},
    'cv.builder_email': {'en': 'Email', 'es': 'Correo'},
    'cv.builder_phone': {'en': 'Phone', 'es': 'Teléfono'},
    'cv.builder_website': {'en': 'Website', 'es': 'Sitio web'},
    'cv.builder_theme': {'en': 'Theme', 'es': 'Tema'},
    'cv.theme_hint': {'en': 'The visual style RenderCV uses to typeset the PDF.', 'es': 'El estilo visual que usa RenderCV para maquetar el PDF.'},
    'cv.social_networks': {'en': 'Social Networks', 'es': 'Redes sociales'},
    'cv.add_social': {'en': '+ Add social network', 'es': '+ Agregar red social'},
    'cv.sections': {'en': 'Sections', 'es': 'Secciones'},
    'cv.sections_hint': {'en': 'Add a section for each part of your CV — Education, Experience, Skills, Projects, Awards…', 'es': 'Agrega una sección por cada parte de tu CV — Educación, Experiencia, Habilidades, Proyectos, Premios…'},
    'cv.add_section': {'en': '+ Add section', 'es': '+ Agregar sección'},

    # ── Gallery ──
    'gallery.title': {'en': 'Gallery', 'es': 'Galería'},
    'gallery.new_photo_btn': {'en': '+ New Photo', 'es': '+ Nueva foto'},
    'gallery.search_ph': {'en': 'Search by title…', 'es': 'Buscar por título…'},
    'gallery.photo': {'en': 'Photo', 'es': 'Foto'},
    'gallery.confirm_delete': {'en': 'Delete photo «{title}»? This cannot be undone.', 'es': '¿Eliminar la foto «{title}»? Esta acción no se puede deshacer.'},
    'gallery.no_photos_match': {'en': 'No photos match "{q}".', 'es': 'Ninguna foto coincide con "{q}".'},
    'gallery.no_photos': {'en': 'No photos yet.', 'es': 'Aún no hay fotos.'},
    'gallery.upload_first': {'en': 'Upload your first photo →', 'es': 'Sube tu primera foto →'},
    'gallery.edit_photo': {'en': 'Edit Photo', 'es': 'Editar foto'},
    'gallery.new_photo': {'en': 'New Photo', 'es': 'Nueva foto'},
    'gallery.photo_details': {'en': 'Photo Details', 'es': 'Detalles de la foto'},
    'gallery.description': {'en': 'Description', 'es': 'Descripción'},
    'gallery.enable_es': {'en': 'Enable Spanish content for this photo', 'es': 'Habilitar contenido en español para esta foto'},
    'gallery.photo_field': {'en': 'Photo', 'es': 'Foto'},
    'gallery.upload_replace_photo': {'en': 'Upload a new file to replace the current photo.', 'es': 'Sube un archivo nuevo para reemplazar la foto actual.'},
    'gallery.new_photo_not_saved': {'en': 'New photo — not saved yet', 'es': 'Nueva foto — aún no guardada'},
    'gallery.upload_photo_btn': {'en': 'Upload Photo', 'es': 'Subir foto'},

    # ── Guestbook ──
    'guestbook.title': {'en': 'Guestbook', 'es': 'Libro de visitas'},
    'guestbook.ip': {'en': 'IP', 'es': 'IP'},
    'guestbook.published': {'en': 'Published', 'es': 'Publicado'},
    'guestbook.pending': {'en': 'Pending', 'es': 'Pendiente'},
    'guestbook.unpublish': {'en': 'Unpublish', 'es': 'Despublicar'},
    'guestbook.approve': {'en': 'Approve', 'es': 'Aprobar'},
    'guestbook.confirm_delete': {'en': 'Delete this guestbook entry? This cannot be undone.', 'es': '¿Eliminar esta entrada del libro de visitas? Esta acción no se puede deshacer.'},
    'guestbook.no_entries': {'en': 'No guestbook entries yet.', 'es': 'Aún no hay entradas en el libro de visitas.'},

    # ── Honeypot ──
    'honeypot.title': {'en': 'Honeypot Log', 'es': 'Registro de honeypot'},
    'honeypot.total_hits': {'en': 'Total Hits', 'es': 'Detecciones totales'},
    'honeypot.today': {'en': 'Today', 'es': 'Hoy'},
    'honeypot.last_7_days': {'en': 'Last 7 Days', 'es': 'Últimos 7 días'},
    'honeypot.unique_ips': {'en': 'Unique IPs', 'es': 'IPs únicas'},
    'honeypot.chart_title': {'en': 'Hits — Last 14 Days', 'es': 'Detecciones — Últimos 14 días'},
    'honeypot.most_active_ips': {'en': 'Most Active IPs', 'es': 'IPs más activas'},
    'honeypot.ip_address': {'en': 'IP Address', 'es': 'Dirección IP'},
    'honeypot.hits': {'en': 'Hits', 'es': 'Detecciones'},
    'honeypot.filter_by_ip': {'en': 'Filter by IP', 'es': 'Filtrar por IP'},
    'honeypot.target_resource': {'en': 'Target Resource', 'es': 'Recurso objetivo'},
    'honeypot.filter_by_ip_title': {'en': 'Filter by this IP', 'es': 'Filtrar por esta IP'},
    'honeypot.filter_by_target': {'en': 'Filter by target', 'es': 'Filtrar por objetivo'},
    'honeypot.matching': {'en': 'matching', 'es': 'coincidencias'},
    'honeypot.total': {'en': 'total', 'es': 'total'},
    'honeypot.page_label': {'en': 'Page', 'es': 'Página'},
    'honeypot.hits_col_title': {'en': 'Hits', 'es': 'Detecciones'},
    'honeypot.showing_n_of': {'en': 'showing {shown} of {total}', 'es': 'mostrando {shown} de {total}'},
    'honeypot.target': {'en': 'Target', 'es': 'Objetivo'},
    'honeypot.user_agent': {'en': 'User Agent', 'es': 'User Agent'},
    'honeypot.method': {'en': 'Method', 'es': 'Método'},
    'honeypot.time': {'en': 'Time', 'es': 'Hora'},
    'honeypot.no_hits_match': {'en': 'No hits match the current filter.', 'es': 'Ninguna detección coincide con el filtro actual.'},
    'honeypot.no_hits': {'en': 'No honeypot hits recorded yet.', 'es': 'Aún no se han registrado detecciones de honeypot.'},
    'honeypot.hit_hash': {'en': 'Honeypot Hit #{id}', 'es': 'Detección de honeypot #{id}'},
    'honeypot.back_to_log': {'en': '← Back to log', 'es': '← Volver al registro'},
    'honeypot.confirm_delete': {'en': 'Delete this honeypot hit? This cannot be undone.', 'es': '¿Eliminar esta detección de honeypot? Esta acción no se puede deshacer.'},
    'honeypot.x_forwarded_for': {'en': 'X-Forwarded-For', 'es': 'X-Forwarded-For'},
    'honeypot.method_path': {'en': 'Method / Path', 'es': 'Método / Ruta'},
    'honeypot.endpoint': {'en': 'Endpoint', 'es': 'Endpoint'},
    'honeypot.referrer': {'en': 'Referrer', 'es': 'Referente'},
    'honeypot.accept_language': {'en': 'Accept-Language', 'es': 'Accept-Language'},
    'honeypot.raw_headers': {'en': 'Raw Request Headers', 'es': 'Cabeceras de la solicitud (raw)'},

    # ── Projects (portfolio) ──
    'projects.title': {'en': 'Portfolio Projects', 'es': 'Proyectos de portafolio'},
    'projects.new_btn': {'en': '+ New Project', 'es': '+ Nuevo proyecto'},
    'projects.search_ph': {'en': 'Search by title…', 'es': 'Buscar por título…'},
    'projects.project_col': {'en': 'Project', 'es': 'Proyecto'},
    'projects.github': {'en': 'GitHub', 'es': 'GitHub'},
    'projects.link': {'en': '↗ link', 'es': '↗ enlace'},
    'projects.repo': {'en': '↗ repo', 'es': '↗ repo'},
    'projects.confirm_delete': {'en': 'Delete project «{title}»? This cannot be undone.', 'es': '¿Eliminar el proyecto «{title}»? Esta acción no se puede deshacer.'},
    'projects.no_match': {'en': 'No projects match "{q}".', 'es': 'Ningún proyecto coincide con "{q}".'},
    'projects.no_projects': {'en': 'No projects yet.', 'es': 'Aún no hay proyectos.'},
    'projects.create_first': {'en': 'Create your first project →', 'es': 'Crea tu primer proyecto →'},
    'projects.edit_title': {'en': 'Edit Project', 'es': 'Editar proyecto'},
    'projects.new_title': {'en': 'New Project', 'es': 'Nuevo proyecto'},
    'projects.details': {'en': 'Project Details', 'es': 'Detalles del proyecto'},
    'projects.excerpt_hint': {'en': 'Short excerpt shown in listings and meta tags.', 'es': 'Extracto breve mostrado en listados y meta tags.'},
    'projects.md_hint': {'en': '.md or .markdown — max 2 MB. Full, detailed write-up shown on the project page.', 'es': '.md o .markdown — máx. 2 MB. Redacción completa y detallada mostrada en la página del proyecto.'},
    'projects.enable_es': {'en': 'Enable Spanish content for this project', 'es': 'Habilitar contenido en español para este proyecto'},
    'projects.project_url': {'en': 'Project URL', 'es': 'URL del proyecto'},
    'projects.github_repo': {'en': 'GitHub Repository', 'es': 'Repositorio de GitHub'},
    'projects.cover_image': {'en': 'Cover Image', 'es': 'Imagen de portada'},
    'projects.upload_replace_cover': {'en': 'Upload a new file to replace the current cover.', 'es': 'Sube un archivo nuevo para reemplazar la portada actual.'},
    'projects.new_cover_not_saved': {'en': 'New cover — not saved yet', 'es': 'Nueva portada — aún no guardada'},
    'projects.create_btn': {'en': 'Create Project', 'es': 'Crear proyecto'},
    'projects.extra_images': {'en': 'Extra Images', 'es': 'Imágenes adicionales'},
    'projects.extra_images_hint': {'en': 'Also shown in the screenshots gallery. Copy a URL to embed it in your Markdown, or use the @filename.ext shorthand.', 'es': 'También se muestran en la galería de capturas. Copia una URL para incrustarla en tu Markdown, o usa el atajo @nombrearchivo.ext.'},
    'projects.no_extra_images': {'en': 'No extra images yet.', 'es': 'Aún no hay imágenes adicionales.'},

    # ── Proyectadas ──
    'proyectadas.title': {'en': 'Proyectadas (personal reflections)', 'es': 'Proyectadas (reflexiones personales)'},
    'proyectadas.new_btn': {'en': '+ New Proyectada', 'es': '+ Nueva proyectada'},
    'proyectadas.text_en_col': {'en': 'Text (EN)', 'es': 'Texto (EN)'},
    'proyectadas.confirm_delete': {'en': 'Delete this proyectada? This cannot be undone.', 'es': '¿Eliminar esta proyectada? Esta acción no se puede deshacer.'},
    'proyectadas.no_items': {'en': 'There are no proyectadas yet.', 'es': 'Aún no hay proyectadas.'},
    'proyectadas.create_first': {'en': 'Create the first one →', 'es': 'Crea la primera →'},
    'proyectadas.edit_title': {'en': 'Edit proyectada', 'es': 'Editar proyectada'},
    'proyectadas.new_title': {'en': 'New proyectada', 'es': 'Nueva proyectada'},
    'proyectadas.detail': {'en': 'Detail', 'es': 'Detalle'},
    'proyectadas.text': {'en': 'Text', 'es': 'Texto'},
    'proyectadas.enable_es': {'en': 'Enable Spanish content for this proyectada', 'es': 'Habilitar contenido en español para esta proyectada'},
    'proyectadas.text_es': {'en': 'Text (ES)', 'es': 'Texto (ES)'},
    'proyectadas.publish_checkbox': {'en': 'Publish (visible on the site)', 'es': 'Publicar (visible en el sitio)'},
    'proyectadas.save_btn': {'en': 'Save changes', 'es': 'Guardar cambios'},
    'proyectadas.create_btn': {'en': 'Create proyectada', 'es': 'Crear proyectada'},

    # ── Visits ──
    'visits.title': {'en': 'Site Visits', 'es': 'Visitas del sitio'},
    'visits.utm_source': {'en': 'UTM Source', 'es': 'Fuente UTM'},
    'visits.chart_title': {'en': 'Traffic — Last 14 Days', 'es': 'Tráfico — Últimos 14 días'},
    'visits.visits_col_title': {'en': 'Visits', 'es': 'Visitas'},
    'visits.visited_at': {'en': 'Visited At', 'es': 'Visitado el'},
    'visits.filter_by_source': {'en': 'Filter by source', 'es': 'Filtrar por fuente'},
    'visits.no_match': {'en': 'No visits match the current filter.', 'es': 'Ninguna visita coincide con el filtro actual.'},
    'visits.no_visits': {'en': 'No visits recorded yet.', 'es': 'Aún no se han registrado visitas.'},

    # ── Backups ──
    'backups.title': {'en': 'Backups', 'es': 'Copias de seguridad'},
    'backups.generate_btn': {'en': '+ Generate Backup', 'es': '+ Generar copia'},
    'backups.website_backups': {'en': 'Website Backups', 'es': 'Copias de seguridad del sitio'},
    'backups.filename': {'en': 'Filename', 'es': 'Nombre del archivo'},
    'backups.size': {'en': 'Size', 'es': 'Tamaño'},
    'backups.confirm_delete': {'en': 'Delete backup «{filename}»? This cannot be undone.', 'es': '¿Eliminar la copia «{filename}»? Esta acción no se puede deshacer.'},
    'backups.explainer': {'en': "Each backup is a row-per-INSERT mysqldump of the database's data only (no table structure) — easy to read, diff, or grep.", 'es': 'Cada copia es un volcado mysqldump fila-por-INSERT solo de los datos de la base (sin estructura de tablas) — fácil de leer, comparar o buscar.'},
    'backups.no_backups': {'en': 'No backups yet. Use the "Generate Backup" button above to create the first one.', 'es': 'Aún no hay copias de seguridad. Usa el botón "Generar copia" de arriba para crear la primera.'},

    # ── Flash messages (Python-side, admin/*.py routes) ──
    'flash.backup_not_found': {'en': 'Backup not found.', 'es': 'Copia de seguridad no encontrada.'},
    'flash.backup_generated': {'en': 'Backup "{filename}" generated ({kb} KB).', 'es': 'Copia "{filename}" generada ({kb} KB).'},
    'flash.backup_deleted': {'en': 'Backup "{filename}" deleted.', 'es': 'Copia "{filename}" eliminada.'},

    'flash.proyectadas_bulk_deleted': {'en': '{n} proyectada(s) deleted.', 'es': '{n} proyectada(s) eliminada(s).'},
    'flash.no_items_selected': {'en': 'No items selected.', 'es': 'No se seleccionaron elementos.'},
    'flash.en_text_required': {'en': 'The English text is required.', 'es': 'El texto en inglés es obligatorio.'},
    'flash.text_too_long': {'en': 'The text cannot exceed 10,000 characters.', 'es': 'El texto no puede superar los 10 000 caracteres.'},
    'flash.proyectada_created': {'en': 'Proyectada created.', 'es': 'Proyectada creada.'},
    'flash.proyectada_not_found': {'en': 'Proyectada not found.', 'es': 'Proyectada no encontrada.'},
    'flash.proyectada_updated': {'en': 'Proyectada updated.', 'es': 'Proyectada actualizada.'},
    'flash.proyectada_deleted': {'en': 'Proyectada deleted.', 'es': 'Proyectada eliminada.'},

    'flash.cv_builder_read_error': {'en': 'Could not read the builder data — please try again.', 'es': 'No se pudieron leer los datos del generador — intenta de nuevo.'},
    'flash.language_required': {'en': 'Language is required.', 'es': 'El idioma es obligatorio.'},
    'flash.name_required': {'en': 'Name is required.', 'es': 'El nombre es obligatorio.'},
    'flash.cv_generation_failed': {'en': 'CV generation failed: {exc}', 'es': 'Error al generar el CV: {exc}'},
    'flash.pdf_required': {'en': 'A PDF file is required.', 'es': 'Se requiere un archivo PDF.'},
    'flash.pdf_rejected': {'en': 'File rejected — must be a PDF and no larger than 10 MB.', 'es': 'Archivo rechazado — debe ser un PDF y no superar los 10 MB.'},
    'flash.cv_uploaded': {'en': 'CV ({lang}) uploaded successfully.', 'es': 'CV ({lang}) subido correctamente.'},
    'flash.cv_not_found': {'en': 'CV not found.', 'es': 'CV no encontrado.'},
    'flash.yaml_required': {'en': 'YAML content is required.', 'es': 'El contenido YAML es obligatorio.'},
    'flash.cv_updated': {'en': 'CV updated successfully.', 'es': 'CV actualizado correctamente.'},
    'flash.cv_deleted': {'en': 'CV ({lang}) deleted.', 'es': 'CV ({lang}) eliminado.'},

    'flash.guestbook_bulk_deleted': {'en': '{n} entrie(s) deleted.', 'es': '{n} entrada(s) eliminada(s).'},
    'flash.no_entries_selected': {'en': 'No entries selected.', 'es': 'No se seleccionaron entradas.'},
    'flash.guestbook_not_found': {'en': 'Entry not found.', 'es': 'Entrada no encontrada.'},
    'flash.guestbook_approved': {'en': 'Entry approved and published.', 'es': 'Entrada aprobada y publicada.'},
    'flash.guestbook_hidden': {'en': "Entry hidden from the public guestbook.", 'es': 'Entrada oculta del guestbook público.'},
    'flash.guestbook_deleted': {'en': 'Entry deleted.', 'es': 'Entrada eliminada.'},

    'flash.gallery_bulk_deleted': {'en': '{n} photo(s) deleted.', 'es': '{n} foto(s) eliminada(s).'},
    'flash.no_photos_selected': {'en': 'No photos selected.', 'es': 'No se seleccionaron fotos.'},
    'flash.title_required': {'en': 'Title is required.', 'es': 'El título es obligatorio.'},
    'flash.image_required': {'en': 'Image is required.', 'es': 'La imagen es obligatoria.'},
    'flash.image_rejected': {'en': 'Image rejected — invalid type or exceeds 5 MB.', 'es': 'Imagen rechazada — tipo inválido o supera los 5 MB.'},
    'flash.photo_created': {'en': 'Photo "{title}" created.', 'es': 'Foto "{title}" creada.'},
    'flash.photo_not_found': {'en': 'Photo not found.', 'es': 'Foto no encontrada.'},
    'flash.photo_updated': {'en': 'Photo updated.', 'es': 'Foto actualizada.'},
    'flash.photo_deleted': {'en': 'Photo "{title}" deleted.', 'es': 'Foto "{title}" eliminada.'},

    'flash.projects_bulk_deleted': {'en': '{n} project(s) deleted.', 'es': '{n} proyecto(s) eliminado(s).'},
    'flash.no_projects_selected': {'en': 'No projects selected.', 'es': 'No se seleccionaron proyectos.'},
    'flash.cover_rejected': {'en': 'Cover image rejected — invalid type or exceeds 5 MB.', 'es': 'Imagen de portada rechazada — tipo inválido o supera los 5 MB.'},
    'flash.en_md_rejected': {'en': 'EN Markdown rejected — must be a .md file under 2 MB.', 'es': 'Markdown EN rechazado — debe ser un archivo .md de menos de 2 MB.'},
    'flash.es_md_rejected': {'en': 'ES Markdown rejected — must be a .md file under 2 MB.', 'es': 'Markdown ES rechazado — debe ser un archivo .md de menos de 2 MB.'},
    'flash.project_created': {'en': 'Project "{title}" created.', 'es': 'Proyecto "{title}" creado.'},
    'flash.project_not_found': {'en': 'Project not found.', 'es': 'Proyecto no encontrado.'},
    'flash.project_updated': {'en': 'Project updated.', 'es': 'Proyecto actualizado.'},
    'flash.project_deleted': {'en': 'Project "{title}" deleted.', 'es': 'Proyecto "{title}" eliminado.'},

    'flash.honeypot_not_found': {'en': 'Honeypot hit not found.', 'es': 'Detección de honeypot no encontrada.'},
    'flash.honeypot_deleted': {'en': 'Honeypot hit deleted.', 'es': 'Detección de honeypot eliminada.'},

    'flash.category_name_required': {'en': 'Category name is required.', 'es': 'El nombre de la categoría es obligatorio.'},
    'flash.category_created': {'en': 'Category "{name}" created.', 'es': 'Categoría "{name}" creada.'},
    'flash.category_not_found': {'en': 'Category not found.', 'es': 'Categoría no encontrada.'},
    'flash.category_updated': {'en': 'Category updated.', 'es': 'Categoría actualizada.'},
    'flash.category_in_use': {'en': 'Cannot delete "{name}" — {n} post(s) are assigned to it.', 'es': 'No se puede eliminar "{name}" — tiene {n} entrada(s) asignada(s).'},
    'flash.category_deleted': {'en': 'Category "{name}" deleted.', 'es': 'Categoría "{name}" eliminada.'},
    'flash.post_created': {'en': 'Post "{title}" created.', 'es': 'Entrada "{title}" creada.'},
    'flash.post_not_found': {'en': 'Post not found.', 'es': 'Entrada no encontrada.'},
    'flash.post_updated': {'en': 'Post updated.', 'es': 'Entrada actualizada.'},
    'flash.post_deleted': {'en': 'Post "{title}" deleted.', 'es': 'Entrada "{title}" eliminada.'},
    'flash.posts_bulk_deleted': {'en': '{n} post(s) deleted.', 'es': '{n} entrada(s) eliminada(s).'},
    'flash.no_posts_selected': {'en': 'No posts selected.', 'es': 'No se seleccionaron entradas.'},

    'flash.message_not_found': {'en': 'Message not found.', 'es': 'Mensaje no encontrado.'},
    'flash.message_deleted': {'en': 'Message deleted.', 'es': 'Mensaje eliminado.'},
    'flash.messages_bulk_deleted': {'en': '{n} message(s) deleted.', 'es': '{n} mensaje(s) eliminado(s).'},
    'flash.no_messages_selected': {'en': 'No messages selected.', 'es': 'No se seleccionaron mensajes.'},
    'flash.blocked_and_deleted': {'en': 'Blocked {email} and deleted {n} message(s).', 'es': 'Se bloqueó {email} y se eliminaron {n} mensaje(s).'},
    'flash.email_or_ip_required': {'en': 'Provide an email and/or an IP address.', 'es': 'Proporciona un correo y/o una dirección IP.'},
    'flash.sender_blocked': {'en': 'Sender blocked.', 'es': 'Remitente bloqueado.'},
    'flash.sender_unblocked': {'en': 'Sender unblocked.', 'es': 'Remitente desbloqueado.'},
}


def t(key: str, **kwargs) -> str:
    """
    Look up an admin-dashboard UI string in the current language and
    interpolate any placeholders (e.g. t('flash.post_deleted', title=post.title)).

    Falls back to English, then to the raw key, so a missing translation
    degrades to visible-but-wrong rather than a hard crash.
    """
    entry = ADMIN_STRINGS.get(key)
    if entry is None:
        return key
    lang = get_current_language()
    text = entry.get(lang, entry.get('en', key))
    return text.format(**kwargs) if kwargs else text
