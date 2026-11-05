"""Tech stack shown on the About page.

Each group is (title_en, title_es, default_color, techs); each tech is
(name, color, name_es). `color` falls back to the group's default and
`name_es` to `name`. Text color (black/white) is derived from the
background, so a new entry only needs a hex color.
"""

TECH_STACK = (
    ('Programming Languages & Scripting', 'Lenguajes de Programación & Scripting', '#546E7A', (
        ('Python', '#3776AB'),
        ('PHP', '#777BB4'),
        ('HTML', '#E34F26'),
        ('CSS', '#1572B6'),
        ('JavaScript', '#F7DF1E'),
        ('TypeScript', '#3178C6'),
        ('SQL', '#CC2927'),
        ('Bash', '#4EAA25'),
        ('Dockerfile', '#2496ED'),
        ('Arduino', '#00979D'),
    )),
    ('Frameworks & Libraries', 'Frameworks & Librerías', '#546E7A', (
        ('React', '#61DAFB'),
        ('React Router', '#CA4245'),
        ('Laravel', '#FF2D20'),
        ('Laravel Reverb', '#FF2D20'),
        ('Livewire', '#FB70A9'),
        ('TailwindCSS', '#06B6D4'),
        ('Vue.js', '#4FC08D'),
        ('Node.js', '#339933'),
        ('Flask', '#000000'),
        ('Django', '#092E20'),
        ('FastAPI', '#009688'),
        ('Alpine.js', '#8BC0D0'),
        ('Chart.js', '#FF6384'),
    )),
    ('Artificial Intelligence', 'Inteligencia Artificial', '#7E57C2', (
        ('Google Gemini API', '#4285F4'),
        ('Gemini Live API', '#1A73E8'),
        ('Function Calling / Tool Use',),
        ('RAG',),
        ('OCR',),
        ('TTS',),
        ('Prompt Engineering',),
        ('Strategy Pattern for AI Report Generation',),
    )),
    ('Methodologies & Management', 'Metodologías & Gestión', '#00897B', (
        ('Agile',),
        ('Scrum',),
        ('Kanban',),
        ('Sprints',),
        ('SDLC',),
        ('Technical Leadership', None, 'Liderazgo Técnico'),
        ('Mentoring',),
        ('Problem Solving', None, 'Resolución de Problemas'),
        ('Troubleshooting',),
    )),
    ('Testing & Quality', 'Testing & Calidad', '#43A047', (
        ('Unit Testing',),
        ('Integration Testing',),
        ('TDD',),
        ('Jest', '#C21325'),
        ('PHPUnit', '#366488'),
        ('PyTest', '#0A9EDC'),
        ('Software Quality', None, 'Calidad de Software'),
        ('Code Review',),
    )),
    ('Infrastructure & Tools', 'Infraestructura & Herramientas', '#546E7A', (
        ('Apache', '#D22128'),
        ('Nginx', '#009639'),
        ('Linux (Ubuntu/Debian/RHEL)', '#FCC624'),
        ('VPS',),
        ('Cloudflare', '#F38020'),
        ('SSL', '#2E7D32'),
        ('DNS', '#1565C0'),
        ('Git', '#F05032'),
        ('GitHub', '#181717'),
        ('GitHub Actions', '#2088FF'),
        ('CI/CD', '#2088FF'),
        ('RESTful APIs', '#0288D1'),
        ('Docker', '#2496ED'),
        ('System Administration', None, 'Administración de Sistemas'),
        ('systemd', '#30D475'),
        ('WebSockets',),
        ('Queue Workers',),
        ('Web Security', '#B71C1C', 'Seguridad Web'),
        ('2FA/TOTP', '#B71C1C'),
        ('SEO', '#F9A825'),
        ('Microservices Architecture', None, 'Arquitectura de Microservicios'),
        ('Multi-tenant SaaS Architecture', None, 'Arquitectura SaaS Multi-tenant'),
    )),
    ('Databases', 'Bases de Datos', '#546E7A', (
        ('MySQL', '#4479A1'),
        ('MariaDB', '#003545'),
        ('SQLite', '#003B57'),
        ('Redis', '#DC382D'),
        ('Oracle Database', '#F80000'),
        ('Cassandra', '#1287B1'),
        ('MongoDB', '#47A248'),
    )),
    ('Platform Deployment', 'Despliegue de Plataformas', '#546E7A', (
        ('AWS S3', '#569A31'),
        ('AWS EC2', '#FF9900'),
        ('AWS SES', '#DD344C'),
        ('Hostinger', '#673DE6'),
        ('WebPay', '#D5007F'),
        ('Stripe', '#635BFF'),
    )),
    ('Networking & Security', 'Redes & Seguridad', '#B71C1C', (
        ('Fortinet', '#EE3124'),
        ('FortiGate', '#EE3124'),
        ('Firewalls',),
        ('VPN', '#455A64'),
    )),
)


def _luminance(hex_color: str) -> float:
    """WCAG relative luminance of a '#RRGGBB' color."""
    channels = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def text_color(background: str) -> str:
    """Black or white, whichever has the higher WCAG contrast against `background`."""
    luminance = _luminance(background)
    return '#000000' if (luminance + 0.05) / 0.05 >= 1.05 / (luminance + 0.05) else '#ffffff'


def get_tech_stack(lang: str) -> list[dict]:
    """TECH_STACK localized for `lang`, with each tag's background and text color resolved."""
    groups = []
    for title_en, title_es, default_color, techs in TECH_STACK:
        tags = []
        for tech in techs:
            name, color, name_es = (tech + (None, None))[:3]
            color = color or default_color
            tags.append({
                'name': (name_es or name) if lang == 'es' else name,
                'bg': color,
                'fg': text_color(color),
            })
        groups.append({'title': title_es if lang == 'es' else title_en, 'tags': tags})
    return groups
