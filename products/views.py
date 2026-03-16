from django.shortcuts import render, get_object_or_404
from .models import Category, Product


def home(request):
    """Landing page — active categories."""
    categories = Category.objects.filter(is_active=True)
    featured = Product.objects.filter(is_active=True)[:8]
    return render(request, 'products/home.html', {
        'categories': categories,
        'featured': featured,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = category.products.filter(is_active=True)
    return render(request, 'products/category_detail.html', {
        'category': category,
        'products': products,
    })


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('configurator_template').prefetch_related(
            'attribute_groups__options',
            'text_fields',
            'sizes',
        ),
        slug=slug,
        is_active=True,
    )
    return render(request, 'products/product_detail.html', {
        'product': product,
    })
