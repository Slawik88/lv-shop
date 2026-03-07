from django.conf import settings


def cart_count(request):
    """Add cart item count to all templates."""
    cart = request.session.get(settings.CART_SESSION_KEY, [])
    return {
        'cart_count': sum(item.get('quantity', 1) for item in cart),
    }
