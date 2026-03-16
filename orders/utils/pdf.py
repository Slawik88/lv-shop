"""
PDF generation for production — creates a work order PDF for manufacturing.
Uses ReportLab. All data comes from the Order/OrderItem/SavedConfiguration models.
"""
import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from orders.models import Order


# ---------------------------------------------------------------------------
# Регистрация шрифта с поддержкой кириллицы — берём из Windows-системных шрифтов
# ---------------------------------------------------------------------------
_FONT_REGISTERED = False
_CYR_FONT = 'Helvetica'  # fallback — ASCII-only, заменим ниже при удаче


def _register_cyrillic_font():
    """Try to register a Cyrillic-capable TTF font once."""
    global _FONT_REGISTERED, _CYR_FONT
    if _FONT_REGISTERED:
        return
    _FONT_REGISTERED = True

    # Порядок поиска: сначала шрифты в папке проекта, затем системные
    candidates = []
    # Windows
    win_fonts = os.environ.get('WINDIR', 'C:\\Windows') + '\\Fonts'
    candidates += [
        os.path.join(win_fonts, 'arial.ttf'),
        os.path.join(win_fonts, 'calibri.ttf'),
        os.path.join(win_fonts, 'times.ttf'),
    ]
    # Linux
    candidates += [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    ]

    for path in candidates:
        if os.path.exists(path):
            try:
                font_name = 'CyrFont'
                pdfmetrics.registerFont(TTFont(font_name, path))
                _CYR_FONT = font_name
                return
            except Exception:
                continue


def generate_order_pdf(order: Order) -> io.BytesIO:
    """Generate a PDF work order for the given Order. Returns a BytesIO buffer."""
    _register_cyrillic_font()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # Custom styles with Cyrillic font
    title_style = ParagraphStyle(
        'OrderTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=10,
        fontName=_CYR_FONT,
    )
    normal = ParagraphStyle('OrderNormal', parent=styles['Normal'], fontName=_CYR_FONT)
    heading2_style = ParagraphStyle('Heading2Cyr', parent=styles['Heading2'], fontName=_CYR_FONT)
    heading3_style = ParagraphStyle('Heading3Cyr', parent=styles['Heading3'], fontName=_CYR_FONT)

    elements = []

    # Header
    elements.append(Paragraph(f'Заказ #{str(order.id)[:8]}', title_style))
    elements.append(Spacer(1, 5*mm))

    # Customer info
    customer_data = [
        ['Клиент:', order.customer_name],
        ['Email:', order.customer_email],
        ['Телефон:', order.customer_phone or '—'],
        ['Адрес:', order.customer_address or '—'],
        ['Статус:', order.get_status_display()],
        ['Дата:', order.created_at.strftime('%d.%m.%Y %H:%M')],
    ]
    customer_table = Table(customer_data, colWidths=[30*mm, 130*mm])
    customer_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 10*mm))

    # Order items
    elements.append(Paragraph('Позиции заказа', heading2_style))
    elements.append(Spacer(1, 3*mm))

    items = order.items.all()
    table_data = [['#', 'Товар', 'Параметры', 'Кол-во', 'Цена']]
    for i, item in enumerate(items, 1):
        # Format configuration summary
        config = item.configuration_summary or {}
        texts = config.get('texts', {})
        options = config.get('options', {})
        params = []
        for k, v in texts.items():
            params.append(f'{k}: {v}')
        for k, v in options.items():
            params.append(f'Опция {k}: {v}')
        param_str = '; '.join(params) if params else '—'

        table_data.append([
            str(i),
            item.product_name,
            param_str,
            str(item.quantity),
            f'{item.price} ₽',
        ])

    # Total row
    table_data.append(['', '', '', 'ИТОГО:', f'{order.total_price} ₽'])

    items_table = Table(table_data, colWidths=[10*mm, 50*mm, 60*mm, 20*mm, 25*mm])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.85, 0.85, 0.85)),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (-2, -1), (-1, -1), 11),
        ('TEXTCOLOR', (-2, -1), (-1, -1), colors.black),
    ]))
    elements.append(items_table)

    # Notes
    if order.notes:
        elements.append(Spacer(1, 10*mm))
        elements.append(Paragraph('Комментарий:', heading3_style))
        elements.append(Paragraph(order.notes, normal))

    doc.build(elements)
    buf.seek(0)
    return buf
