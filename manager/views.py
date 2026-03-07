from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from orders.models import Order
from products.models import (
    AttributeGroup, AttributeOption, Category, Product,
    ProductSize, TextFieldConfig,
)
from .forms import (
    AttributeGroupForm, AttributeOptionForm, CategoryForm,
    ProductForm, ProductSizeForm, TextFieldConfigForm,
)


# ---------------------------------------------------------------------------
# Auth decorator
# ---------------------------------------------------------------------------

def staff_required(view_func):
    """Require login AND is_staff; raises 403 otherwise."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@staff_required
def dashboard(request):
    categories = Category.objects.all().order_by('sort_order', 'name')
    products = Product.objects.select_related('category').order_by('-id')
    recent_orders = Order.objects.prefetch_related('items').order_by('-created_at')[:10]
    return render(request, 'manager/dashboard.html', {
        'categories': categories,
        'products': products,
        'recent_orders': recent_orders,
    })


# ---------------------------------------------------------------------------
# Category CRUD
# ---------------------------------------------------------------------------

@staff_required
def category_list(request):
    categories = Category.objects.all().order_by('sort_order', 'name')
    return render(request, 'manager/category_list.html', {'categories': categories})


@staff_required
def category_create(request):
    form = CategoryForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save()
        messages.success(request, f'Категория «{cat.name}» создана.')
        return redirect('manager:category_list')
    return render(request, 'manager/category_form.html', {
        'form': form,
        'title': 'Новая категория',
        'action': 'Создать',
    })


@staff_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, request.FILES or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Категория «{cat.name}» сохранена.')
        return redirect('manager:category_list')
    return render(request, 'manager/category_form.html', {
        'form': form,
        'object': cat,
        'title': f'Редактировать: {cat.name}',
        'action': 'Сохранить',
    })


@staff_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = cat.name
        cat.delete()
        messages.success(request, f'Категория «{name}» удалена.')
        return redirect('manager:category_list')
    return render(request, 'manager/confirm_delete.html', {
        'object': cat,
        'object_name': cat.name,
        'cancel_url': reverse('manager:category_list'),
    })


# ---------------------------------------------------------------------------
# Product CRUD
# ---------------------------------------------------------------------------

@staff_required
def product_list(request):
    products = Product.objects.select_related('category').order_by('category__sort_order', 'name')
    return render(request, 'manager/product_list.html', {'products': products})


@staff_required
def product_create(request):
    form = ProductForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        messages.success(request, f'Товар «{product.name}» создан.')
        return redirect('manager:product_options', slug=product.slug)
    return render(request, 'manager/product_form.html', {
        'form': form,
        'title': 'Новый товар',
        'action': 'Создать',
    })


@staff_required
def product_edit(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Товар «{product.name}» сохранён.')
        return redirect('manager:product_list')
    return render(request, 'manager/product_form.html', {
        'form': form,
        'object': product,
        'title': f'Редактировать: {product.name}',
        'action': 'Сохранить',
    })


@staff_required
def product_delete(request, slug):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'Товар «{name}» удалён.')
        return redirect('manager:product_list')
    return render(request, 'manager/confirm_delete.html', {
        'object': product,
        'object_name': product.name,
        'cancel_url': reverse('manager:product_list'),
    })


# ---------------------------------------------------------------------------
# Product Options (attribute groups, text fields, sizes)
# ---------------------------------------------------------------------------

@staff_required
def product_options(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'attribute_groups__options', 'text_fields', 'sizes',
        ),
        slug=slug,
    )
    return render(request, 'manager/product_options.html', {'product': product})


# ----- Attribute Groups -----

@staff_required
def attribute_group_create(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = AttributeGroupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        group.product = product
        group.save()
        messages.success(request, f'Группа «{group.name}» добавлена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/attribute_group_form.html', {
        'form': form, 'product': product,
        'title': 'Новая группа атрибутов', 'action': 'Создать',
    })


@staff_required
def attribute_group_edit(request, slug, group_id):
    product = get_object_or_404(Product, slug=slug)
    group = get_object_or_404(AttributeGroup, id=group_id, product=product)
    form = AttributeGroupForm(request.POST or None, instance=group)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Группа обновлена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/attribute_group_form.html', {
        'form': form, 'product': product,
        'title': f'Редактировать группу: {group.name}', 'action': 'Сохранить',
    })


@staff_required
def attribute_group_delete(request, slug, group_id):
    product = get_object_or_404(Product, slug=slug)
    group = get_object_or_404(AttributeGroup, id=group_id, product=product)
    if request.method == 'POST':
        name = group.name
        group.delete()
        messages.success(request, f'Группа «{name}» удалена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/confirm_delete.html', {
        'object': group,
        'object_name': group.name,
        'cancel_url': reverse('manager:product_options', kwargs={'slug': slug}),
    })


# ----- Attribute Options -----

@staff_required
def attribute_option_create(request, slug, group_id):
    product = get_object_or_404(Product, slug=slug)
    group = get_object_or_404(AttributeGroup, id=group_id, product=product)
    form = AttributeOptionForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        option = form.save(commit=False)
        option.group = group
        option.save()
        messages.success(request, f'Опция «{option.name}» добавлена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/attribute_option_form.html', {
        'form': form, 'product': product, 'group': group,
        'title': f'Новая опция для «{group.name}»', 'action': 'Создать',
    })


@staff_required
def attribute_option_edit(request, slug, group_id, option_id):
    product = get_object_or_404(Product, slug=slug)
    group = get_object_or_404(AttributeGroup, id=group_id, product=product)
    option = get_object_or_404(AttributeOption, id=option_id, group=group)
    form = AttributeOptionForm(request.POST or None, request.FILES or None, instance=option)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Опция обновлена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/attribute_option_form.html', {
        'form': form, 'product': product, 'group': group,
        'title': f'Редактировать опцию: {option.name}', 'action': 'Сохранить',
    })


@staff_required
def attribute_option_delete(request, slug, group_id, option_id):
    product = get_object_or_404(Product, slug=slug)
    group = get_object_or_404(AttributeGroup, id=group_id, product=product)
    option = get_object_or_404(AttributeOption, id=option_id, group=group)
    if request.method == 'POST':
        name = option.name
        option.delete()
        messages.success(request, f'Опция «{name}» удалена.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/confirm_delete.html', {
        'object': option,
        'object_name': option.name,
        'cancel_url': reverse('manager:product_options', kwargs={'slug': slug}),
    })


# ----- Text Fields -----

@staff_required
def text_field_create(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = TextFieldConfigForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tf = form.save(commit=False)
        tf.product = product
        tf.save()
        messages.success(request, f'Текстовое поле «{tf.label}» добавлено.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/text_field_form.html', {
        'form': form, 'product': product,
        'title': 'Новое текстовое поле', 'action': 'Создать',
    })


@staff_required
def text_field_edit(request, slug, tf_id):
    product = get_object_or_404(Product, slug=slug)
    tf = get_object_or_404(TextFieldConfig, id=tf_id, product=product)
    form = TextFieldConfigForm(request.POST or None, instance=tf)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Текстовое поле обновлено.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/text_field_form.html', {
        'form': form, 'product': product,
        'title': f'Редактировать поле: {tf.label}', 'action': 'Сохранить',
    })


@staff_required
def text_field_delete(request, slug, tf_id):
    product = get_object_or_404(Product, slug=slug)
    tf = get_object_or_404(TextFieldConfig, id=tf_id, product=product)
    if request.method == 'POST':
        label = tf.label
        tf.delete()
        messages.success(request, f'Поле «{label}» удалено.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/confirm_delete.html', {
        'object': tf,
        'object_name': tf.label,
        'cancel_url': reverse('manager:product_options', kwargs={'slug': slug}),
    })


# ----- Sizes -----

@staff_required
def size_create(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ProductSizeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        size = form.save(commit=False)
        size.product = product
        size.save()
        messages.success(request, f'Размер «{size.name}» добавлен.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/size_form.html', {
        'form': form, 'product': product,
        'title': 'Новый размер', 'action': 'Создать',
    })


@staff_required
def size_edit(request, slug, size_id):
    product = get_object_or_404(Product, slug=slug)
    size = get_object_or_404(ProductSize, id=size_id, product=product)
    form = ProductSizeForm(request.POST or None, instance=size)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Размер обновлён.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/size_form.html', {
        'form': form, 'product': product,
        'title': f'Редактировать размер: {size.name}', 'action': 'Сохранить',
    })


@staff_required
def size_delete(request, slug, size_id):
    product = get_object_or_404(Product, slug=slug)
    size = get_object_or_404(ProductSize, id=size_id, product=product)
    if request.method == 'POST':
        name = size.name
        size.delete()
        messages.success(request, f'Размер «{name}» удалён.')
        return redirect('manager:product_options', slug=slug)
    return render(request, 'manager/confirm_delete.html', {
        'object': size,
        'object_name': size.name,
        'cancel_url': reverse('manager:product_options', kwargs={'slug': slug}),
    })


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@staff_required
def order_list(request):
    orders = Order.objects.prefetch_related('items').order_by('-created_at')
    return render(request, 'manager/order_list.html', {'orders': orders})


@staff_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=['status'])
            messages.success(request, 'Статус заказа обновлён.')
            return redirect('manager:order_detail', pk=pk)
    return render(request, 'manager/order_detail.html', {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
    })
