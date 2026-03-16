import json
from decimal import Decimal

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET, require_POST

from products.models import Product, ProductSize
from .models import ConfiguratorTemplate, FontChoice, SavedConfiguration


@require_GET
def preview_svg(request, product_slug):
    """
    Generate a dynamic SVG preview based on current configuration.
    All coordinates, fonts, and colors come from DB — ZERO HARDCODE.

    Query params:
        text_<field_id>=<value>  — text field values
        option_<group_id>=<option_id>  — selected options
        font=<font_name>  — override font
        pos_<field_id>=x,y  — override text position (customer drag)
        show_grid=1  — overlay a ruler grid for WYSIWYG editing
    """
    product = get_object_or_404(
        Product.objects.prefetch_related('text_fields', 'attribute_groups__options'),
        slug=product_slug,
        is_active=True,
    )
    template = ConfiguratorTemplate.objects.filter(product=product).first()
    if template is None:
        # Product has no configurator template — return a placeholder SVG so the
        # frontend never gets a 404. Show the product image if one exists.
        return _placeholder_svg(product, request)
    text_fields = product.text_fields.all()
    layers = template.layers_config or {}

    width = template.width
    height = template.height
    bg_color = layers.get('background_color', '#ffffff')

    # Resolve selected options for color groups.
    # If a color option has its own image — it becomes the product background (shows real product in that color).
    # Otherwise fall back to a color-tint overlay.
    selected_color_hex = None
    selected_option_image = None  # AttributeOption.image for the elected option
    for group in product.attribute_groups.all():
        option_id = request.GET.get(f'option_{group.id}')
        if option_id and group.widget_type == 'color':
            for opt in group.options.all():
                if str(opt.id) == str(option_id):
                    if opt.image:
                        selected_option_image = opt.image
                    elif opt.color_hex:
                        selected_color_hex = opt.color_hex
                    break
            break  # first color group wins

    # Build SVG
    svg_id = f'svg-{product_slug}'
    svg_parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" id="{svg_id}" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="display:block;max-width:100%;height:auto;">',
    ]

    # Background
    border_radius = layers.get('border_radius', 0)
    svg_parts.append(
        f'<rect width="{width}" height="{height}" fill="{bg_color}" rx="{border_radius}"/>'
    )

    # Product image layer — priority: selected option image > template base_image > product image
    if selected_option_image:
        opt_img_url = request.build_absolute_uri(selected_option_image.url)
        svg_parts.append(
            f'<image href="{_escape_svg_attr(opt_img_url)}" '
            f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" '
            f'clip-path="inset(0 round {border_radius}px)"/>'
        )
    elif template.base_image:
        bg_img_url = request.build_absolute_uri(template.base_image.url)
        svg_parts.append(
            f'<image href="{_escape_svg_attr(bg_img_url)}" '
            f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice" '
            f'clip-path="inset(0 round {border_radius}px)"/>'
        )
    elif product.image and product.image.name:
        bg_img_url = request.build_absolute_uri(product.image.url)
        svg_parts.append(
            f'<image href="{_escape_svg_attr(bg_img_url)}" '
            f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet"/>'
        )

    # Color tint overlay — only applied when there is NO per-option image
    if selected_color_hex and not selected_option_image:
        escaped_hex = _escape_svg_attr(selected_color_hex)
        svg_parts.append(
            f'<rect width="{width}" height="{height}" fill="{escaped_hex}" '
            f'opacity="0.3" rx="{border_radius}"/>'
        )

    # Extra decorations from layers_config
    for deco in layers.get('extra_decorations', []):
        deco_type = deco.get('type', '')
        if deco_type == 'line':
            svg_parts.append(
                f'<line x1="{deco["x1"]}" y1="{deco["y1"]}" '
                f'x2="{deco["x2"]}" y2="{deco["y2"]}" '
                f'stroke="{deco.get("stroke", "#ccc")}" '
                f'stroke-width="{deco.get("stroke_width", 1)}"/>'
            )
        elif deco_type == 'rect':
            svg_parts.append(
                f'<rect x="{deco["x"]}" y="{deco["y"]}" '
                f'width="{deco["w"]}" height="{deco["h"]}" '
                f'fill="{deco.get("fill", "none")}" '
                f'stroke="{deco.get("stroke", "#ccc")}"/>'
            )

    # Overlay mask
    if template.overlay_mask:
        opacity = layers.get('overlay_opacity', 0.5)
        svg_parts.append(
            f'<image href="{_escape_svg_attr(request.build_absolute_uri(template.overlay_mask.url))}" '
            f'width="{width}" height="{height}" opacity="{opacity}" '
            f'preserveAspectRatio="xMidYMid meet"/>'
        )

    # Grid overlay (for WYSIWYG editor mode) — now in CENTIMETERS
    if request.GET.get('show_grid') == '1':
        # Calculate pixels per centimeter based on real dimensions
        real_w_cm = float(template.real_width_cm) if template.real_width_cm else 20.0
        real_h_cm = float(template.real_height_cm) if template.real_height_cm else 15.0
        px_per_cm_x = width / real_w_cm
        px_per_cm_y = height / real_h_cm
        
        grid_color = 'rgba(100,80,60,0.12)'
        tick_color = 'rgba(100,80,60,0.35)'
        
        # Draw centimeter grid lines (vertical)
        for cm in range(1, int(real_w_cm) + 1):
            x = cm * px_per_cm_x
            if x < width:
                svg_parts.append(f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{height}" stroke="{grid_color}" stroke-width="1"/>')
                # Label every 5 cm
                if cm % 5 == 0:
                    svg_parts.append(f'<text x="{x+3}" y="12" font-size="9" fill="{tick_color}" font-family="monospace">{cm}cm</text>')
        
        # Draw centimeter grid lines (horizontal)
        for cm in range(1, int(real_h_cm) + 1):
            y = cm * px_per_cm_y
            if y < height:
                svg_parts.append(f'<line x1="0" y1="{y:.1f}" x2="{width}" y2="{y:.1f}" stroke="{grid_color}" stroke-width="1"/>')
                # Label every 5 cm
                if cm % 5 == 0:
                    svg_parts.append(f'<text x="3" y="{y-3}" font-size="9" fill="{tick_color}" font-family="monospace">{cm}cm</text>')
        
        # Center crosshair
        cx, cy = width / 2, height / 2
        svg_parts.append(f'<line x1="{cx:.1f}" y1="0" x2="{cx:.1f}" y2="{height}" stroke="rgba(188,138,84,.3)" stroke-width="1" stroke-dasharray="4 3"/>')
        svg_parts.append(f'<line x1="0" y1="{cy:.1f}" x2="{width}" y2="{cy:.1f}" stroke="rgba(188,138,84,.3)" stroke-width="1" stroke-dasharray="4 3"/>')
        
        # Show dimensions badge
        svg_parts.append(
            f'<rect x="{width-80}" y="{height-22}" width="75" height="18" rx="4" fill="rgba(255,252,248,.9)"/>'
            f'<text x="{width-42}" y="{height-10}" font-size="10" fill="#bc8a54" font-family="monospace" text-anchor="middle">'
            f'{real_w_cm:.0f}×{real_h_cm:.0f} cm</text>'
        )

    # Global font override
    font_override = request.GET.get('font', '')

    # Text layers — with optional position overrides from customer drag
    for tf in text_fields:
        text_value = request.GET.get(f'text_{tf.id}', tf.placeholder or tf.label)
        font_family = font_override or tf.preview_font_family
        color = tf.preview_color

        # Optional per-field color from selected option
        color_param = request.GET.get(f'color_{tf.id}')
        if color_param and color_param.startswith('#'):
            color = color_param

        # Customer-dragged position override
        pos_x, pos_y = tf.preview_x, tf.preview_y
        pos_param = request.GET.get(f'pos_{tf.id}')
        if pos_param and ',' in pos_param:
            try:
                px, py = pos_param.split(',', 1)
                pos_x = float(px)
                pos_y = float(py)
            except (ValueError, TypeError):
                pass

        # Per-field font size override from customer slider
        size_override = request.GET.get(f'size_{tf.id}')
        try:
            field_font_size = max(6.0, min(200.0, float(size_override))) if size_override else tf.preview_font_size
        except (ValueError, TypeError):
            field_font_size = tf.preview_font_size

        # Bold/italic style overrides
        font_weight = 'bold' if request.GET.get(f'bold_{tf.id}') == '1' else 'normal'
        font_style = 'italic' if request.GET.get(f'italic_{tf.id}') == '1' else 'normal'

        escaped = _escape_svg(text_value)

        svg_parts.append(
            f'<text data-field-id="{tf.id}" '
            f'x="{pos_x}" y="{pos_y}" '
            f'font-family="{_escape_svg_attr(font_family)}" font-size="{field_font_size}" '
            f'font-weight="{font_weight}" font-style="{font_style}" '
            f'fill="{_escape_svg_attr(color)}" text-anchor="{_escape_svg_attr(tf.preview_text_anchor)}" '
            f'dominant-baseline="middle" '
            f'style="cursor:move;user-select:none;">'
            f'{escaped}</text>'
        )

    svg_parts.append('</svg>')

    svg_content = '\n'.join(svg_parts)
    return HttpResponse(svg_content, content_type='image/svg+xml')


@require_GET
def calculate_price(request, product_slug):
    """
    HTMX endpoint — recalculate price based on selected options.
    Returns an HTML partial with the updated price.
    """
    product = get_object_or_404(
        Product.objects.prefetch_related('attribute_groups__options'),
        slug=product_slug,
        is_active=True,
    )
    total = product.base_price

    # Build option-id → price_modifier map in one pass (no N+1)
    option_price_map = {}
    group_option_ids = {}
    for group in product.attribute_groups.all():  # uses prefetch cache
        option_id = request.GET.get(f'option_{group.id}')
        if option_id:
            group_option_ids[group.id] = option_id
        for opt in group.options.all():  # uses prefetch cache
            option_price_map[str(opt.id)] = opt.price_modifier

    for option_id in group_option_ids.values():
        modifier = option_price_map.get(str(option_id))
        if modifier is not None:
            total += modifier

    # Add size modifier if provided
    size_id = request.GET.get('size_id')
    if size_id:
        try:
            size = ProductSize.objects.get(id=int(size_id), product=product)
            total += size.price_modifier
        except (ProductSize.DoesNotExist, ValueError, TypeError):
            pass

    return render(request, 'configurator/partials/price.html', {
        'total': total,
        'product': product,
    })


@require_GET
def get_fonts(request):
    """Return available fonts as JSON (for Alpine.js dropdown)."""
    fonts = FontChoice.objects.filter(is_active=True).values('id', 'name', 'css_family')
    return JsonResponse(list(fonts), safe=False)


@require_POST
def save_configuration(request, product_slug):
    """
    Save the complete product configuration to DB.
    Returns the SavedConfiguration ID for cart use.
    """
    product = get_object_or_404(Product, slug=product_slug, is_active=True)

    try:
        config_data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # Calculate price server-side — never trust client price
    # Build option lookup in one pass to avoid N+1 queries
    total = product.base_price
    options_selected = config_data.get('options', {})  # {str(group_id): str(option_id)}

    option_price_map = {}  # str(option_id) -> price_modifier
    for group in product.attribute_groups.prefetch_related('options').all():
        for opt in group.options.all():  # uses prefetch cache
            option_price_map[str(opt.id)] = opt.price_modifier

    for group_id, option_id in options_selected.items():
        modifier = option_price_map.get(str(option_id))
        if modifier is not None:
            total += modifier

    # Add size modifier if provided
    size_id = config_data.get('size_id')
    if size_id:
        try:
            size = ProductSize.objects.get(id=int(size_id), product=product)
            total += size.price_modifier
        except (ProductSize.DoesNotExist, ValueError, TypeError):
            pass

    saved = SavedConfiguration.objects.create(
        product=product,
        configuration=config_data,
        calculated_price=total,
    )

    return JsonResponse({
        'id': str(saved.id),
        'price': str(saved.calculated_price),
    })


def _placeholder_svg(product, request):
    """Return a minimal static SVG for products that have no ConfiguratorTemplate."""
    width, height = 600, 400
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" style="display:block;max-width:100%;height:auto;">',
        f'<rect width="{width}" height="{height}" fill="#f5ede2" rx="12"/>',
    ]
    if product.image and product.image.name:
        img_url = request.build_absolute_uri(product.image.url)
        parts.append(
            f'<image href="{_escape_svg_attr(img_url)}" '
            f'width="{width}" height="{height}" preserveAspectRatio="xMidYMid meet" '
            f'clip-path="inset(0 round 12px)"/>'
        )
    else:
        escaped_name = _escape_svg(product.name)
        parts.append(
            f'<text x="{width // 2}" y="{height // 2}" font-family="Arial,sans-serif" '
            f'font-size="22" fill="#9a7860" text-anchor="middle" dominant-baseline="middle">'
            f'{escaped_name}</text>'
        )
    parts.append('</svg>')
    return HttpResponse('\n'.join(parts), content_type='image/svg+xml')


def _escape_svg(text: str) -> str:
    """Escape special HTML/SVG chars for SVG text *content*."""
    return (
        str(text)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
    )


def _escape_svg_attr(value: str) -> str:
    """Escape a value for use inside an SVG attribute (double-quoted)."""
    return (
        str(value)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#39;')
    )
