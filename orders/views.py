import json
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from configurator.models import SavedConfiguration
from .models import Order, OrderItem


# ---------------------------------------------------------------------------
# Cart helpers (session-based)
# ---------------------------------------------------------------------------

def _get_cart(request):
    return request.session.get(settings.CART_SESSION_KEY, [])


def _save_cart(request, cart):
    request.session[settings.CART_SESSION_KEY] = cart
    request.session.modified = True


def _enrich_cart(cart):
    """Return a new list with computed `line_total` for each item (does NOT mutate session data)."""
    result = []
    for item in cart:
        enriched = dict(item)
        enriched['line_total'] = Decimal(item['price']) * item['quantity']
        result.append(enriched)
    return result


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

@require_POST
def add_to_cart(request):
    """Add a saved configuration to the session cart."""
    config_id = request.POST.get('configuration_id')
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        quantity = 1

    if not config_id:
        return JsonResponse({'error': 'configuration_id required'}, status=400)

    try:
        config = SavedConfiguration.objects.select_related('product').get(id=config_id)
    except SavedConfiguration.DoesNotExist:
        return JsonResponse({'error': 'Configuration not found'}, status=404)

    cart = _get_cart(request)

    # Check if already in cart
    for item in cart:
        if item['config_id'] == config_id:
            item['quantity'] += quantity
            _save_cart(request, cart)
            return _cart_response(request, cart)

    cart.append({
        'config_id': str(config.id),
        'product_name': config.product.name,
        'product_slug': config.product.slug,
        'price': str(config.calculated_price),
        'quantity': quantity,
        'configuration': config.configuration,
    })
    _save_cart(request, cart)
    return _cart_response(request, cart)


def cart_view(request):
    """Display cart contents."""
    raw_cart = _get_cart(request)
    cart = _enrich_cart(raw_cart)
    total = sum(item['line_total'] for item in cart)
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'total': total,
    })


@require_POST
def remove_from_cart(request, index):
    """Remove item from cart by index."""
    cart = _get_cart(request)
    if 0 <= index < len(cart):
        cart.pop(index)
        _save_cart(request, cart)
    return redirect('orders:cart')


@require_POST
def update_cart_quantity(request, index):
    """HTMX endpoint — update quantity for a cart item, returns full cart partial."""
    cart = _get_cart(request)
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (ValueError, TypeError):
        quantity = 1

    if 0 <= index < len(cart):
        cart[index]['quantity'] = quantity
        _save_cart(request, cart)

    enriched = _enrich_cart(cart)
    total = sum(item['line_total'] for item in enriched)
    return render(request, 'orders/partials/cart_content.html', {
        'cart': enriched,
        'total': total,
    })


def checkout(request):
    """Checkout form & order creation."""
    raw_cart = _get_cart(request)
    if not raw_cart:
        messages.warning(request, 'Добавьте товары в корзину перед оформлением заказа.')
        return redirect('orders:cart')

    if request.method == 'POST':
        customer_name = request.POST.get('name', '').strip()
        customer_email = request.POST.get('email', '').strip()
        if not customer_name or not customer_email:
            messages.error(request, 'Пожалуйста, заполните обязательные поля.')
            cart = _enrich_cart(raw_cart)
            total = sum(item['line_total'] for item in cart)
            return render(request, 'orders/checkout.html', {'cart': cart, 'total': total})

        order = Order.objects.create(
            customer_name=customer_name,
            customer_email=customer_email,
            customer_phone=request.POST.get('phone', '').strip(),
            customer_address=request.POST.get('address', '').strip(),
            notes=request.POST.get('notes', '').strip(),
        )

        for item in raw_cart:
            config = None
            try:
                config = SavedConfiguration.objects.get(id=item['config_id'])
            except (SavedConfiguration.DoesNotExist, Exception):
                pass

            OrderItem.objects.create(
                order=order,
                configuration=config,
                product_name=item['product_name'],
                configuration_summary=item.get('configuration', {}),
                quantity=item['quantity'],
                price=Decimal(item['price']),
            )

        order.recalculate_total()
        _save_cart(request, [])
        return redirect('orders:order_success', order_id=order.id)

    cart = _enrich_cart(raw_cart)
    total = sum(item['line_total'] for item in cart)
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'total': total,
    })


def order_success(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
    return render(request, 'orders/order_success.html', {'order': order})


def _cart_response(request, cart):
    """Return HTMX-friendly response after cart modification."""
    if request.headers.get('HX-Request'):
        enriched = _enrich_cart(cart)
        total = sum(item['line_total'] for item in enriched)
        return render(request, 'orders/partials/cart_mini.html', {
            'cart': enriched,
            'total': total,
        })
    return redirect('orders:cart')


def order_pdf(request, order_id):
    """Download production PDF for an order."""
    from .utils.pdf import generate_order_pdf
    order = get_object_or_404(Order.objects.prefetch_related('items'), id=order_id)
    buf = generate_order_pdf(order)
    response = HttpResponse(buf.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{str(order.id)[:8]}.pdf"'
    return response
