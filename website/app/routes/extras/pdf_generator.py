import os
from io import BytesIO
from datetime import datetime

from flask import current_app, request, send_file
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF

from faker import Faker
from random import randint, uniform, choice

from app.routes.extras import extras_bp
from app.i18n import get_current_language, render_localized_template

# ─── Colour palette ───────────────────────────────────────────────────────────
NAVY  = colors.HexColor('#1a1a2e')
RED   = colors.HexColor('#DE0000')
DGRAY = colors.HexColor('#333333')
MGRAY = colors.HexColor('#666666')
LGRAY = colors.HexColor('#cccccc')
LLGRAY = colors.HexColor('#f0f0f0')
WHITE = colors.white

# ─── Localised copy ───────────────────────────────────────────────────────────
STRINGS = {
    'en': {
        'company':         'AstronautMarkus Corp.',
        'department':      'Office of Strategic Planning',
        'doc_light_title': 'Summary Report',
        'doc_heavy_title': 'Consolidated Corporate Report',
        'doc_subtitle':    'Internal Use Only',
        'confidential':    'CONFIDENTIAL',
        'prepared_by':     'Prepared by',
        'author':          'Systems Division — AstronautMarkus Corp.',
        'date_label':      'Date',
        'page_label':      'Page',
        'of_label':        'of',
        'toc_title':       'Table of Contents',
        'toc_entries': [
            ('1. Executive Summary', 3),
            ('2. Financial Overview', 4),
            ('3. Technical Specifications', 5),
            ('4. Legal Notice & Disclaimer', 6),
        ],
        'exec_title':    '1. Executive Summary',
        'finance_title': '2. Financial Overview',
        'tech_title':    '3. Technical Specifications',
        'legal_title':   '4. Legal Notice & Disclaimer',
        'highlights_title': 'Key Highlights',
        'exec_body': [
            'AstronautMarkus Corp. has experienced continued growth across all divisions during the '
            'reporting period. This document provides a comprehensive overview of operational activities, '
            'financial performance, and strategic initiatives undertaken by the organisation.',

            'The Systems Division has successfully deployed three major infrastructure upgrades, resulting '
            'in a 40 % reduction in response latency and improved uptime metrics across all production '
            'environments. These improvements are a direct result of sustained investment in modern DevOps '
            'practices and a culture of continuous delivery.',

            'Customer satisfaction indices have reached an all-time high of 94.7 %, reflecting the '
            'organisation\'s commitment to service excellence and continuous improvement. The support team '
            'handled 12,847 tickets during the quarter, maintaining an average resolution time of under '
            '4 hours — well below the industry benchmark of 8 hours.',

            'Looking ahead, the Board of Directors has approved a significant capital allocation towards '
            'cloud-native architecture modernisation and talent acquisition in the cybersecurity domain. '
            'These initiatives are expected to yield measurable returns within the next two fiscal quarters '
            'and will reinforce the organisation\'s competitive positioning in the market.',
        ],
        'exec_highlights': [
            'Revenue growth: +18.3 % year-over-year',
            'Active deployments: 247 across 12 regions',
            'Employee headcount: 1,204  (↑ 89 from last quarter)',
            'Net Promoter Score (NPS): 72 — industry leading',
            'Incident SLA compliance: 99.1 %',
        ],
        'finance_headers': ['Quarter', 'Revenue (USD)', 'Expenses (USD)', 'Net Profit (USD)', 'Margin'],
        'finance_rows': [
            ['Q1 2025', '$2,140,800', '$1,580,200', '$560,600',   '26.2 %'],
            ['Q2 2025', '$2,390,000', '$1,620,000', '$770,000',   '32.2 %'],
            ['Q3 2025', '$2,715,400', '$1,790,300', '$925,100',   '34.1 %'],
            ['Q4 2025', '$3,102,900', '$1,970,150', '$1,132,750', '36.5 %'],
            ['Q1 2026', '$3,480,000', '$2,105,000', '$1,375,000', '39.5 %'],
            ['TOTAL',   '$13,829,100', '$9,065,650', '$4,763,450', '34.4 %'],
        ],
        'tech_headers': ['Component', 'Specification', 'Status'],
        'tech_rows': [
            ['Web Server',    'Nginx 1.27 + Gunicorn 23.0',   'Operational'],
            ['Application',   'Python 3.12 / Flask 3.1',      'Operational'],
            ['Database',      'MySQL 8.0 / MariaDB 10.11',    'Operational'],
            ['Storage',       'S3-compatible (MinIO)',         'Operational'],
            ['Container',     'Docker 27 / Compose v2',       'Operational'],
            ['CI/CD',         'GitHub Actions + systemd',     'Operational'],
            ['Monitoring',    'Prometheus + Grafana',          'Planned Q3 2026'],
            ['CDN',           'Cloudflare Free Tier',          'Operational'],
            ['Auth',          'Flask-Login + bcrypt',          'Operational'],
            ['Mail',          'SMTP via Flask-Mail',           'Operational'],
        ],
        'light_overview_title': 'Document Overview',
        'light_overview': (
            'This summary report has been generated as a lightweight placeholder document for '
            'testing, integration, and demonstration purposes. It does not contain any sensitive '
            'or proprietary information. All figures and references are entirely fictional.'
        ),
        'light_section1_title': 'Operational Status',
        'light_section1': (
            'All core systems are reported as fully operational with no critical incidents logged '
            'during the current reporting window. Routine maintenance windows have been completed '
            'on schedule. Infrastructure capacity remains within acceptable thresholds.'
        ),
        'light_section2_title': 'Next Steps',
        'light_section2': (
            'The team is proceeding with planned roadmap items as outlined in the Q2 2026 '
            'strategy document. No blockers have been identified at this time. A full consolidated '
            'report will be issued at the end of the fiscal quarter.'
        ),
        'legal_body': (
            'This document and all information contained herein is the exclusive property of '
            'AstronautMarkus Corp. and is classified as CONFIDENTIAL. Unauthorised reproduction, '
            'distribution, or disclosure of this document, in any form or by any means, is strictly '
            'prohibited without prior written consent of AstronautMarkus Corp.\n\n'
            'All financial figures, projections, and operational data presented in this report are '
            'for illustrative purposes only and do not represent actual financial results or '
            'commitments of any real organisation. Any resemblance to actual events, companies, or '
            'financial data is purely coincidental.\n\n'
            'AstronautMarkus Corp. makes no warranties, express or implied, regarding the accuracy, '
            'completeness, or fitness for a particular purpose of any information contained herein. '
            'In no event shall AstronautMarkus Corp., its officers, directors, or employees be liable '
            'for any direct, indirect, incidental, or consequential damages arising from the use of '
            'this document.\n\n'
            'This is a dummy PDF generated by AstronautMarkus.dev for testing and demonstration '
            'purposes. It contains no real corporate, financial, or personal data. By accessing this '
            'document you agree to treat its contents as entirely fictional.\n\n'
            '© 2026 AstronautMarkus Corp. All rights reserved. WTFPL applies where applicable.'
        ),
    },
    'es': {
        'company':         'AstronautMarkus Corp.',
        'department':      'Oficina de Planificación Estratégica',
        'doc_light_title': 'Informe de Resumen',
        'doc_heavy_title': 'Informe Corporativo Consolidado',
        'doc_subtitle':    'Solo Uso Interno',
        'confidential':    'CONFIDENCIAL',
        'prepared_by':     'Preparado por',
        'author':          'División de Sistemas — AstronautMarkus Corp.',
        'date_label':      'Fecha',
        'page_label':      'Página',
        'of_label':        'de',
        'toc_title':       'Tabla de Contenidos',
        'toc_entries': [
            ('1. Resumen Ejecutivo', 3),
            ('2. Panorama Financiero', 4),
            ('3. Especificaciones Técnicas', 5),
            ('4. Aviso Legal y Descargo', 6),
        ],
        'exec_title':    '1. Resumen Ejecutivo',
        'finance_title': '2. Panorama Financiero',
        'tech_title':    '3. Especificaciones Técnicas',
        'legal_title':   '4. Aviso Legal y Descargo de Responsabilidad',
        'highlights_title': 'Puntos Clave',
        'exec_body': [
            'AstronautMarkus Corp. ha experimentado un crecimiento sostenido en todas sus divisiones '
            'durante el período reportado. Este documento ofrece una visión integral de las actividades '
            'operacionales, el desempeño financiero y las iniciativas estratégicas emprendidas por la '
            'organización.',

            'La División de Sistemas ha implementado con éxito tres actualizaciones mayores de '
            'infraestructura, lo que ha resultado en una reducción del 40 % en la latencia de respuesta '
            'y en una mejora en las métricas de disponibilidad en todos los entornos de producción. '
            'Estas mejoras son fruto de la inversión sostenida en prácticas modernas de DevOps y en una '
            'cultura de entrega continua.',

            'Los índices de satisfacción del cliente han alcanzado un máximo histórico del 94,7 %, '
            'reflejando el compromiso de la organización con la excelencia en el servicio y la mejora '
            'continua. El equipo de soporte gestionó 12.847 tickets durante el trimestre, manteniendo '
            'un tiempo promedio de resolución inferior a 4 horas, muy por debajo del estándar del sector.',

            'De cara al futuro, la Junta Directiva ha aprobado una asignación significativa de capital '
            'para la modernización de la arquitectura cloud-native y la incorporación de talento en el '
            'ámbito de la ciberseguridad. Se espera que estas iniciativas generen retornos medibles en '
            'los próximos dos trimestres fiscales y consoliden el posicionamiento competitivo de la '
            'organización en el mercado.',
        ],
        'exec_highlights': [
            'Crecimiento de ingresos: +18,3 % interanual',
            'Despliegues activos: 247 en 12 regiones',
            'Dotación de personal: 1.204  (↑ 89 vs. trimestre anterior)',
            'Net Promoter Score (NPS): 72 — líder del sector',
            'Cumplimiento SLA de incidencias: 99,1 %',
        ],
        'finance_headers': ['Trimestre', 'Ingresos (USD)', 'Gastos (USD)', 'Beneficio Neto (USD)', 'Margen'],
        'finance_rows': [
            ['T1 2025', '$2.140.800', '$1.580.200', '$560.600',     '26,2 %'],
            ['T2 2025', '$2.390.000', '$1.620.000', '$770.000',     '32,2 %'],
            ['T3 2025', '$2.715.400', '$1.790.300', '$925.100',     '34,1 %'],
            ['T4 2025', '$3.102.900', '$1.970.150', '$1.132.750',   '36,5 %'],
            ['T1 2026', '$3.480.000', '$2.105.000', '$1.375.000',   '39,5 %'],
            ['TOTAL',   '$13.829.100', '$9.065.650', '$4.763.450',  '34,4 %'],
        ],
        'tech_headers': ['Componente', 'Especificación', 'Estado'],
        'tech_rows': [
            ['Servidor Web',      'Nginx 1.27 + Gunicorn 23.0',   'Operacional'],
            ['Aplicación',        'Python 3.12 / Flask 3.1',      'Operacional'],
            ['Base de Datos',     'MySQL 8.0 / MariaDB 10.11',    'Operacional'],
            ['Almacenamiento',    'S3-compatible (MinIO)',         'Operacional'],
            ['Contenedor',        'Docker 27 / Compose v2',       'Operacional'],
            ['CI/CD',             'GitHub Actions + systemd',     'Operacional'],
            ['Monitoreo',         'Prometheus + Grafana',          'Planificado T3 2026'],
            ['CDN',               'Cloudflare Plan Gratuito',     'Operacional'],
            ['Autenticación',     'Flask-Login + bcrypt',          'Operacional'],
            ['Correo',            'SMTP vía Flask-Mail',           'Operacional'],
        ],
        'light_overview_title': 'Descripción del Documento',
        'light_overview': (
            'Este informe de resumen ha sido generado como documento de relleno ligero para fines de '
            'prueba, integración y demostración. No contiene información sensible ni propietaria. '
            'Todas las cifras y referencias son completamente ficticias.'
        ),
        'light_section1_title': 'Estado Operacional',
        'light_section1': (
            'Todos los sistemas principales se encuentran completamente operacionales y no se han '
            'registrado incidencias críticas durante la ventana de reporte actual. Las ventanas de '
            'mantenimiento de rutina se han completado dentro del plazo previsto. La capacidad de '
            'infraestructura se mantiene dentro de umbrales aceptables.'
        ),
        'light_section2_title': 'Próximos Pasos',
        'light_section2': (
            'El equipo continúa trabajando en los ítems planificados del roadmap descritos en el '
            'documento de estrategia T2 2026. No se han identificado bloqueos en este momento. Se '
            'emitirá un informe consolidado completo al cierre del trimestre fiscal.'
        ),
        'legal_body': (
            'Este documento y toda la información contenida en él es propiedad exclusiva de '
            'AstronautMarkus Corp. y está clasificado como CONFIDENCIAL. La reproducción, distribución '
            'o divulgación no autorizada de este documento, en cualquier forma o por cualquier medio, '
            'está estrictamente prohibida sin el consentimiento previo por escrito de AstronautMarkus Corp.\n\n'
            'Todas las cifras financieras, proyecciones y datos operacionales presentados en este informe '
            'son meramente ilustrativos y no representan resultados financieros reales ni compromisos de '
            'ninguna organización real. Cualquier parecido con eventos reales, empresas o datos financieros '
            'es pura coincidencia.\n\n'
            'AstronautMarkus Corp. no ofrece garantías, expresas o implícitas, sobre la exactitud, '
            'integridad o idoneidad para un fin particular de la información contenida en este documento. '
            'En ningún caso AstronautMarkus Corp., sus directivos o empleados serán responsables de '
            'daños directos, indirectos, incidentales o consecuentes derivados del uso de este documento.\n\n'
            'Este es un PDF ficticio generado por AstronautMarkus.dev con fines de prueba y demostración. '
            'No contiene datos corporativos, financieros ni personales reales. Al acceder a este documento '
            'usted acepta tratar su contenido como completamente ficticio.\n\n'
            '© 2026 AstronautMarkus Corp. Todos los derechos reservados. WTFPL aplicable donde corresponda.'
        ),
    },
}


# ─── Style helpers ────────────────────────────────────────────────────────────

def _build_styles(lang: str) -> dict:
    base = getSampleStyleSheet()

    def p(name, **kw):
        return ParagraphStyle(name, parent=base['Normal'], **kw)

    return {
        # Cover — dark text on white background, Tux as logo header
        'cover_company':  p('cc',  fontSize=28, fontName='Helvetica-Bold', textColor=NAVY,
                             leading=36, alignment=TA_CENTER, spaceAfter=6),
        'cover_dept':     p('cd',  fontSize=12, fontName='Helvetica', textColor=MGRAY,
                             leading=18, alignment=TA_CENTER, spaceAfter=4),
        'cover_title':    p('ct',  fontSize=20, fontName='Helvetica-Bold', textColor=NAVY,
                             leading=26, alignment=TA_CENTER, spaceAfter=6),
        'cover_subtitle': p('cs',  fontSize=11, fontName='Helvetica', textColor=MGRAY,
                             leading=16, alignment=TA_CENTER, spaceAfter=4),
        'cover_conf':     p('cco', fontSize=12, fontName='Helvetica-Bold', textColor=RED,
                             leading=16, alignment=TA_CENTER, spaceAfter=0),
        # Body
        'section_title':  p('st',  fontSize=16, fontName='Helvetica-Bold', textColor=NAVY,
                             spaceBefore=14, spaceAfter=6, borderPad=0),
        'body':           p('b',   fontSize=10, textColor=DGRAY, leading=16,
                             alignment=TA_JUSTIFY, spaceAfter=8),
        'bullet':         p('bl',  fontSize=10, textColor=DGRAY, leading=15,
                             leftIndent=14, spaceAfter=4,
                             bulletIndent=0, bulletFontName='Helvetica', bulletFontSize=10),
        # TOC
        'toc_entry':      p('te',  fontSize=11, textColor=DGRAY, leading=20),
        'toc_title':      p('tt',  fontSize=18, fontName='Helvetica-Bold', textColor=NAVY,
                             spaceAfter=20, spaceBefore=0),
        # Table header
        'th':             p('th',  fontSize=9, fontName='Helvetica-Bold', textColor=WHITE,
                             alignment=TA_CENTER),
        'td':             p('tdc', fontSize=9, textColor=DGRAY, alignment=TA_CENTER),
        # Light doc
        'light_company':  p('lc',  fontSize=24, fontName='Helvetica-Bold', textColor=NAVY,
                             leading=32, spaceAfter=8),
        'light_doc':      p('ld',  fontSize=16, fontName='Helvetica', textColor=MGRAY,
                             leading=22, spaceAfter=4),
        'light_meta':     p('lm',  fontSize=9, textColor=MGRAY, leading=14, spaceAfter=0),
    }


# ─── Random data + charts helpers ──────────────────────────────────────────
def _generate_fake_data(lang: str) -> dict:
    fake = Faker('es_ES' if lang == 'es' else 'en_US')
    title = fake.company()
    author = fake.name()
    points = [round(uniform(1000, 5500) * (1 + i * uniform(0.01, 0.15)), 2) for i in range(6)]
    categories = [fake.month_name()[:3].capitalize() for _ in range(6)]
    peak = max(points)
    avg = round(sum(points) / len(points), 2)
    return {
        'gen_title': title,
        'gen_author': author,
        'points': points,
        'categories': categories,
        'peak': peak,
        'avg': avg,
    }


def _make_chart(data: list, categories: list, width_cm: float = 14, height_cm: float = 6,
                kind: str = 'line') -> Drawing:
    w = width_cm * cm
    h = height_cm * cm
    drawing = Drawing(w, h)
    if kind == 'bar':
        bc = VerticalBarChart()
        bc.x = 40
        bc.y = 10
        bc.height = h - 30
        bc.width = w - 80
        bc.data = [data]
        bc.categoryAxis.categoryNames = categories
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = max(data) * 1.2
        bc.valueAxis.valueStep = max(1, int(max(data) // 5))
        drawing.add(bc)
    else:
        lp = LinePlot()
        lp.x = 40
        lp.y = 10
        lp.height = h - 30
        lp.width = w - 80
        pts = list(enumerate(data, start=1))
        lp.data = [pts]
        lp.lines[0].strokeWidth = 1.5
        drawing.add(lp)

    drawing.add(String(w / 2, h - 8, 'Auto-generated chart', textAnchor='middle', fontSize=9))
    return drawing


# ─── Year replacement helper ───────────────────────────────────────────────
def _replace_years(obj):
    y = str(datetime.now().year)
    if isinstance(obj, str):
        return obj.replace('2026', y)
    elif isinstance(obj, dict):
        return {k: _replace_years(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_years(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(_replace_years(v) for v in obj)
    else:
        return obj


# ─── Page number canvas ───────────────────────────────────────────────────────

class _NumberedCanvas(pdfcanvas.Canvas):
    """Adds page numbers in the footer. On the heavy PDF's cover page (page 1)
    the footer is intentionally omitted — the background is painted by the
    onFirstPage callback so it sits *behind* the flowables."""

    def __init__(self, *args, pdf_lang='en', has_cover=False, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: list = []
        self._lang = pdf_lang
        self._has_cover = has_cover

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved_page_states)
        s = _replace_years(STRINGS[self._lang])
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber == 1 and self._has_cover:
                pass  # no footer on cover; background already drawn by onFirstPage
            else:
                self._draw_footer(self._pageNumber, n, s)
            pdfcanvas.Canvas.showPage(self)
        pdfcanvas.Canvas.save(self)

    def _draw_footer(self, page_num: int, total: int, s: dict):
        self.saveState()
        self.setFont('Helvetica', 8)
        self.setFillColor(MGRAY)
        w, _ = A4
        self.drawString(2 * cm, 1.4 * cm, s['company'])
        self.drawRightString(w - 2 * cm, 1.4 * cm,
                             f"{s['page_label']} {page_num} {s['of_label']} {total}")
        self.setStrokeColor(LGRAY)
        self.setLineWidth(0.5)
        self.line(2 * cm, 1.7 * cm, w - 2 * cm, 1.7 * cm)
        self.restoreState()


# ─── Light PDF ────────────────────────────────────────────────────────────────

def _build_light(buf: BytesIO, lang: str) -> None:
    s = _replace_years(STRINGS[lang])
    styles = _build_styles(lang)
    page_w, page_h = A4
    date_str = datetime.now().strftime('%B %d, %Y') if lang == 'en' \
        else datetime.now().strftime('%d de %B de %Y')

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.8 * cm,
        title=f'{s["company"]} — {s["doc_light_title"]}',
        author=s['author'],
        subject=s['doc_subtitle'],
    )

    story = []

    # ── Document header ──────────────────────────────────────────────────────
    story.append(Paragraph(s['company'].upper(), styles['light_company']))
    story.append(Paragraph(s['doc_light_title'], styles['light_doc']))
    story.append(Paragraph(
        f"{s['date_label']}: {date_str}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{s['prepared_by']}: {s['author']}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"{s['doc_subtitle']}",
        styles['light_meta'],
    ))
    story.append(HRFlowable(width='100%', thickness=3, color=RED, spaceBefore=8, spaceAfter=20))

    # ── Section 1 ────────────────────────────────────────────────────────────
    story.append(Paragraph(s['light_overview_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=1, color=LLGRAY, spaceAfter=8))
    story.append(Paragraph(s['light_overview'], styles['body']))
    story.append(Spacer(1, 0.3 * cm))

    # ── Section 2 ────────────────────────────────────────────────────────────
    story.append(Paragraph(s['light_section1_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=1, color=LLGRAY, spaceAfter=8))
    story.append(Paragraph(s['light_section1'], styles['body']))
    story.append(Spacer(1, 0.3 * cm))

    # ── Section 3 ────────────────────────────────────────────────────────────
    story.append(Paragraph(s['light_section2_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=1, color=LLGRAY, spaceAfter=8))
    story.append(Paragraph(s['light_section2'], styles['body']))
    story.append(Spacer(1, 0.5 * cm))

    # ── Confidential stamp ───────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=8))
    conf_style = ParagraphStyle('conf', parent=getSampleStyleSheet()['Normal'],
                                fontSize=9, fontName='Helvetica-Bold', textColor=RED,
                                alignment=TA_CENTER)
    story.append(Paragraph(s['confidential'], conf_style))

    # Insert small auto-generated snapshot and chart to make each PDF unique
    gen = _generate_fake_data(lang)
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"Snapshot: {gen['gen_title']} — {gen['gen_author']}", styles['light_meta']))
    chart = _make_chart(gen['points'], gen['categories'], width_cm=14, height_cm=5,
                        kind=choice(['line', 'bar']))
    story.append(Spacer(1, 0.2 * cm))
    story.append(chart)

    doc.build(
        story,
        canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, pdf_lang=lang, **kw),
    )


# ─── Heavy PDF ────────────────────────────────────────────────────────────────

def _build_heavy(buf: BytesIO, lang: str) -> None:
    s = _replace_years(STRINGS[lang])
    styles = _build_styles(lang)
    page_w, page_h = A4
    date_str = datetime.now().strftime('%B %d, %Y') if lang == 'en' \
        else datetime.now().strftime('%d de %B de %Y')

    try:
        root_path = current_app.root_path
    except Exception:
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    tux_path = os.path.join(root_path, 'static', 'images', 'tux.png')

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=2.5 * cm, bottomMargin=2.8 * cm,
        title=f'{s["company"]} — {s["doc_heavy_title"]}',
        author=s['author'],
        subject=s['doc_subtitle'],
    )

    story = []

    # ─── Page 1 — Cover ───────────────────────────────────────────────────────
    # Clean white background. Tux acts as the corporate logo header.

    # ── Tux logo ─────────────────────────────────────────────────────────────
    if os.path.isfile(tux_path):
        try:
            img = RLImage(tux_path, width=7 * cm, height=7 * cm)
            img.hAlign = 'CENTER'
            story.append(Spacer(1, 1 * cm))
            story.append(img)
            story.append(Spacer(1, 0.5 * cm))
        except Exception:
            story.append(Spacer(1, 2 * cm))
    else:
        story.append(Spacer(1, 2 * cm))

    story.append(HRFlowable(width='100%', thickness=3, color=RED, spaceAfter=12))
    story.append(Paragraph(s['company'].upper(), styles['cover_company']))
    story.append(Paragraph(s['department'], styles['cover_dept']))
    story.append(Spacer(1, 0.8 * cm))

    # Red divider
    divider = Table([['']], colWidths=[14 * cm], rowHeights=[0.15 * cm])
    divider.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), RED)]))
    divider.hAlign = 'CENTER'
    story.append(divider)
    story.append(Spacer(1, 0.8 * cm))

    story.append(Paragraph(s['doc_heavy_title'], styles['cover_title']))
    story.append(Paragraph(s['doc_subtitle'], styles['cover_subtitle']))
    story.append(Spacer(1, 1.8 * cm))
    story.append(Paragraph(f"{s['date_label']}: {date_str}", styles['cover_subtitle']))
    story.append(Paragraph(f"{s['prepared_by']}: {s['author']}", styles['cover_subtitle']))
    story.append(Spacer(1, 1.2 * cm))
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=10))
    story.append(Paragraph(s['confidential'], styles['cover_conf']))

    story.append(PageBreak())

    # ─── Page 2 — Table of Contents ───────────────────────────────────────────
    story.append(Paragraph(s['toc_title'], styles['toc_title']))
    story.append(HRFlowable(width='100%', thickness=3, color=RED, spaceAfter=20))

    for entry_name, page_num in s['toc_entries']:
        dots = '.' * 60
        toc_row = Table(
            [[Paragraph(entry_name, styles['toc_entry']),
              Paragraph(str(page_num), styles['toc_entry'])]],
            colWidths=[13 * cm, 2 * cm],
        )
        toc_row.setStyle(TableStyle([
            ('ALIGN',        (1, 0), (1, 0), 'RIGHT'),
            ('LINEBELOW',    (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
            ('TOPPADDING',   (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
        ]))
        story.append(toc_row)

    story.append(PageBreak())

    # ─── Page 3 — Executive Summary ───────────────────────────────────────────
    story.append(Paragraph(s['exec_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=12))

    for para in s['exec_body']:
        story.append(Paragraph(para, styles['body']))

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(s['highlights_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=1, color=LLGRAY, spaceAfter=8))

    for point in s['exec_highlights']:
        story.append(Paragraph(f'• {point}', styles['bullet']))

    # Auto-generated snapshot to vary outputs
    gen = _generate_fake_data(lang)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(f"Snapshot: {gen['gen_title']} — Avg: ${gen['avg']}", styles['body']))
    chart = _make_chart(gen['points'], gen['categories'], width_cm=14, height_cm=6,
                        kind=choice(['line', 'bar']))
    story.append(Spacer(1, 0.3 * cm))
    story.append(chart)

    story.append(PageBreak())

    # ─── Page 4 — Financial Overview ──────────────────────────────────────────
    story.append(Paragraph(s['finance_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=16))

    headers = [Paragraph(h, styles['th']) for h in s['finance_headers']]
    rows = [[Paragraph(cell, styles['td']) for cell in row]
            for row in s['finance_rows']]
    table_data = [headers] + rows

    col_w = [3 * cm, 3.2 * cm, 3.2 * cm, 3.6 * cm, 2 * cm]
    finance_table = Table(table_data, colWidths=col_w, repeatRows=1)
    finance_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',   (0, 0), (-1, 0),  NAVY),
        ('TEXTCOLOR',    (0, 0), (-1, 0),  WHITE),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',     (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0),  9),
        # Data rows
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LLGRAY]),
        ('FONTSIZE',     (0, 1), (-1, -1), 9),
        # Total row
        ('BACKGROUND',   (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('FONTNAME',     (0, -1), (-1, -1), 'Helvetica-Bold'),
        # Borders
        ('GRID',         (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LINEBELOW',    (0, 0), (-1, 0),  1.5, RED),
        ('TOPPADDING',   (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 6),
    ]))
    story.append(finance_table)
    story.append(PageBreak())

    # ─── Page 5 — Technical Specifications ────────────────────────────────────
    story.append(Paragraph(s['tech_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=16))

    tech_headers = [Paragraph(h, styles['th']) for h in s['tech_headers']]
    tech_rows = [[Paragraph(cell, styles['td']) for cell in row]
                 for row in s['tech_rows']]
    tech_data = [tech_headers] + tech_rows

    tech_col_w = [4.5 * cm, 7 * cm, 3.5 * cm]
    tech_table = Table(tech_data, colWidths=tech_col_w, repeatRows=1)
    tech_table.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0),  NAVY),
        ('TEXTCOLOR',      (0, 0), (-1, 0),  WHITE),
        ('ALIGN',          (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME',       (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, 0),  9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, LLGRAY]),
        ('FONTSIZE',       (0, 1), (-1, -1), 9),
        ('GRID',           (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('LINEBELOW',      (0, 0), (-1, 0),  1.5, RED),
        ('TOPPADDING',     (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING',  (0, 0), (-1, -1), 6),
    ]))
    story.append(tech_table)
    story.append(PageBreak())

    # ─── Page 6 — Legal Notice ────────────────────────────────────────────────
    story.append(Paragraph(s['legal_title'], styles['section_title']))
    story.append(HRFlowable(width='100%', thickness=2, color=RED, spaceAfter=16))

    legal_style = ParagraphStyle(
        'legal', parent=getSampleStyleSheet()['Normal'],
        fontSize=9, textColor=MGRAY, leading=14,
        alignment=TA_JUSTIFY, spaceAfter=10,
    )
    for block in s['legal_body'].split('\n\n'):
        story.append(Paragraph(block.replace('\n', ' '), legal_style))

    def _on_cover_page(canvas, doc):
        """Draw a thin red top-bar accent on the cover page."""
        canvas.saveState()
        w, h = A4
        canvas.setFillColor(RED)
        canvas.rect(0, h - 0.35 * cm, w, 0.35 * cm, fill=1, stroke=0)
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=_on_cover_page,
        canvasmaker=lambda *a, **kw: _NumberedCanvas(*a, pdf_lang=lang, has_cover=True, **kw),
    )

def generate_pdf(mode: str, lang: str) -> bytes:
    buf = BytesIO()
    if mode == 'heavy':
        _build_heavy(buf, lang)
    else:
        _build_light(buf, lang)
    return buf.getvalue()


# ─── Route ────────────────────────────────────────────────────────────────────

@extras_bp.route('/extras/pdf-generator', methods=['GET', 'POST'])
def pdf_generator():
    if request.method == 'POST':
        mode = request.form.get('mode', 'light')
        if mode not in ('light', 'heavy'):
            mode = 'light'
        lang = get_current_language()
        pdf_bytes = generate_pdf(mode, lang)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'dummy_{mode}_{ts}.pdf'
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename,
        )
    return render_localized_template('main/pdf_generator.html')
