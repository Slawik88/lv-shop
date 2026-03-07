"""
PDF generation for production — creates a work order PDF for manufacturing.
Uses ReportLab. All data comes from the Order/OrderItem/SavedConfiguration models.
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from orders.models import Order


def generate_order_pdf(order: Order) -> io.BytesIO:
    """Generate a PDF work order for the given Order. Returns a BytesIO buffer."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'OrderTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=10,
    )
    normal = styles['Normal']

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
    elements.append(Paragraph('Позиции заказа', styles['Heading2']))
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
        elements.append(Paragraph('Комментарий:', styles['Heading3']))
        elements.append(Paragraph(order.notes, normal))

    doc.build(elements)
    buf.seek(0)
    return buf
