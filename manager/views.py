import base64
import io
import re
import uuid
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

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
# Auth helpers
# ---------------------------------------------------------------------------

LOGIN_URL = '/manager/login/'


def superuser_required(view_func):
    """
    Require login AND is_superuser.
    Unauthenticated users are redirected to the manager login page.
    Authenticated non-superusers get a 403.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'{LOGIN_URL}?next={request.get_full_path()}')
        if not request.user.is_superuser:
            raise PermissionDenied('Доступ только для администраторов')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_login(request):
    """Login page for the admin panel — superusers only."""
    from django.contrib.auth import authenticate, login as auth_login

    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('manager:dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            auth_login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or ''
            # Validate next is a local path to prevent open-redirect
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('manager:dashboard')
        elif user is not None and not user.is_superuser:
            error = 'Доступ только для администраторов сайта.'
        else:
            error = 'Неверный логин или пароль.'

    return render(request, 'manager/login.html', {
        'error': error,
        'next': request.GET.get('next', ''),
    })


def manager_logout(request):
    """Log out and redirect to the manager login page."""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return redirect('manager:login')


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@superuser_required
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

@superuser_required
def category_list(request):
    from django.db.models import Count
    categories = (
        Category.objects
        .annotate(products_count=Count('products'))
        .order_by('sort_order', 'name')
    )
    return render(request, 'manager/category_list.html', {'categories': categories})


@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
def product_list(request):
    products = Product.objects.select_related('category').order_by('category__sort_order', 'name')
    return render(request, 'manager/product_list.html', {'products': products})


@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
def product_options(request, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'attribute_groups__options', 'text_fields', 'sizes',
        ),
        slug=slug,
    )
    return render(request, 'manager/product_options.html', {'product': product})


# ----- Attribute Groups -----

@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
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


@superuser_required
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


@superuser_required
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

@superuser_required
def order_list(request):
    orders = Order.objects.prefetch_related('items').order_by('-created_at')
    return render(request, 'manager/order_list.html', {'orders': orders})


@superuser_required
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


# ---------------------------------------------------------------------------
# Image Studio
# ---------------------------------------------------------------------------

@superuser_required
def image_studio(request):
    """Image preparation studio — resize, crop, colour-correct, apply to products."""
    products = Product.objects.filter(is_active=True).order_by('category__sort_order', 'name')
    options = (
        AttributeOption.objects
        .select_related('group__product')
        .filter(group__widget_type__in=['color', 'image'])
        .order_by('group__product__name', 'group__name', 'sort_order')
    )
    return render(request, 'manager/image_studio.html', {
        'products': products,
        'options': options,
    })


@superuser_required
@require_POST
def image_studio_process(request):
    """
    Process an uploaded image with Pillow.
    Returns JSON: { preview: "data:...", width, height, size_kb }
    Saves processed result to media/studio_tmp/<token>.<ext> for the apply step.
    """
    from PIL import Image, ImageEnhance, ImageOps

    # ── Load source ───────────────────────────────────────────────────────────
    if 'image' in request.FILES:
        uploaded = request.FILES['image']
        if uploaded.size > 20 * 1024 * 1024:
            return JsonResponse({'error': 'Файл слишком большой (макс. 20 МБ)'}, status=400)
        try:
            img = Image.open(uploaded)
            img.verify()          # confirm it is actually an image
            uploaded.seek(0)
            img = Image.open(uploaded)
            img.load()
        except Exception:
            return JsonResponse({'error': 'Не удалось открыть файл как изображение'}, status=400)

        # Persist original to studio_tmp/orig_<token>.png so subsequent
        # re-process calls don't need another upload.
        orig_buf = io.BytesIO()
        src_copy = img.copy()
        if src_copy.mode not in ('RGB', 'RGBA'):
            src_copy = src_copy.convert('RGBA')
        src_copy.save(orig_buf, format='PNG')

        # Clean up previous original temp file
        old_orig = request.session.get('studio_orig_token')
        if old_orig:
            old_path = f'studio_tmp/orig_{old_orig}.png'
            if default_storage.exists(old_path):
                default_storage.delete(old_path)

        orig_token = uuid.uuid4().hex[:16]
        default_storage.save(f'studio_tmp/orig_{orig_token}.png',
                             ContentFile(orig_buf.getvalue()))
        request.session['studio_orig_token'] = orig_token
    else:
        orig_token = request.session.get('studio_orig_token')
        orig_path = f'studio_tmp/orig_{orig_token}.png' if orig_token else ''
        if not orig_token or not default_storage.exists(orig_path):
            return JsonResponse({'error': 'Изображение не загружено. Загрузите файл снова.'}, status=400)
        with default_storage.open(orig_path, 'rb') as f:
            img = Image.open(io.BytesIO(f.read()))
            img.load()

    # ── Validate & parse parameters ───────────────────────────────────────────
    def _int(key, default, lo=1, hi=8000):
        try:
            return max(lo, min(hi, int(request.POST.get(key, default))))
        except (TypeError, ValueError):
            return default

    def _float(key, default, lo=0.0, hi=5.0):
        try:
            return max(lo, min(hi, float(request.POST.get(key, default))))
        except (TypeError, ValueError):
            return default

    width      = _int('width', 600)
    height     = _int('height', 400)
    fit        = request.POST.get('fit', 'cover')
    if fit not in ('cover', 'contain', 'stretch'):
        fit = 'cover'
    bg_hex     = request.POST.get('bg_color', '#ffffff')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', bg_hex):
        bg_hex = '#ffffff'
    out_fmt    = request.POST.get('format', 'png')
    if out_fmt not in ('jpeg', 'png', 'webp'):
        out_fmt = 'png'
    quality    = _int('quality', 90, 10, 100)
    brightness = _float('brightness', 1.0, 0.1, 3.0)
    contrast   = _float('contrast',   1.0, 0.1, 3.0)
    sharpness  = _float('sharpness',  1.0, 0.0, 5.0)
    rotate_deg = _int('rotate', 0, 0, 360)
    if rotate_deg not in (0, 90, 180, 270):
        rotate_deg = 0
    flip_h = request.POST.get('flip_h') == '1'

    # ── Convert to RGBA working mode ──────────────────────────────────────────
    if img.mode == 'P':
        img = img.convert('RGBA')
    elif img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    working = img.convert('RGBA') if img.mode != 'RGBA' else img.copy()

    # ── Transform ─────────────────────────────────────────────────────────────
    if rotate_deg:
        working = working.rotate(-rotate_deg, expand=True)  # negative = clockwise
    if flip_h:
        working = ImageOps.mirror(working)

    # ── Resize / fit ──────────────────────────────────────────────────────────
    def _bg_rgba(hex_str):
        r = int(hex_str[1:3], 16)
        g = int(hex_str[3:5], 16)
        b = int(hex_str[5:7], 16)
        return (r, g, b, 255)

    if fit == 'cover':
        working = ImageOps.fit(working, (width, height), Image.LANCZOS)
    elif fit == 'contain':
        working.thumbnail((width, height), Image.LANCZOS)
        canvas = Image.new('RGBA', (width, height), _bg_rgba(bg_hex))
        px = (width - working.width) // 2
        py = (height - working.height) // 2
        canvas.paste(working, (px, py), working)
        working = canvas
    else:  # stretch
        working = working.resize((width, height), Image.LANCZOS)

    # ── Colour corrections (act on RGB bands, preserve alpha) ─────────────────
    r_ch, g_ch, b_ch, a_ch = working.split()
    rgb = Image.merge('RGB', (r_ch, g_ch, b_ch))
    if brightness != 1.0:
        rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    if contrast != 1.0:
        rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    if sharpness != 1.0:
        rgb = ImageEnhance.Sharpness(rgb).enhance(sharpness)
    r2, g2, b2 = rgb.split()
    working = Image.merge('RGBA', (r2, g2, b2, a_ch))

    # ── Convert to output colour mode ─────────────────────────────────────────
    ext_map = {'jpeg': 'jpg', 'png': 'png', 'webp': 'webp'}
    fmt_pil = {'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP'}
    if out_fmt == 'jpeg':
        bg_rgb = Image.new('RGB', working.size, (255, 255, 255))
        bg_rgb.paste(working, mask=working.split()[3])
        final = bg_rgb
    else:
        final = working  # PNG / WebP keep RGBA

    # ── Encode ────────────────────────────────────────────────────────────────
    buf = io.BytesIO()
    save_kw = {}
    if out_fmt in ('jpeg', 'webp'):
        save_kw['quality'] = quality
    if out_fmt == 'jpeg':
        save_kw['optimize'] = True
    final.save(buf, format=fmt_pil[out_fmt], **save_kw)
    processed = buf.getvalue()

    # ── Save to temp file ─────────────────────────────────────────────────────
    ext = ext_map[out_fmt]
    old_token  = request.session.get('studio_token')
    old_format = request.session.get('studio_format', 'png')
    if old_token:
        old_path = f'studio_tmp/{old_token}.{ext_map.get(old_format, "png")}'
        if default_storage.exists(old_path):
            default_storage.delete(old_path)

    token    = uuid.uuid4().hex[:16]
    tmp_path = f'studio_tmp/{token}.{ext}'
    default_storage.save(tmp_path, ContentFile(processed))
    request.session['studio_token']  = token
    request.session['studio_format'] = out_fmt

    mime = {'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}[out_fmt]
    return JsonResponse({
        'preview':  f'data:{mime};base64,{base64.b64encode(processed).decode()}',
        'width':    final.width,
        'height':   final.height,
        'size_kb':  round(len(processed) / 1024, 1),
    })


@superuser_required
@require_POST
def image_studio_apply(request):
    """Save the processed temp image to a product's or option's image field."""
    token  = request.session.get('studio_token')
    fmt    = request.session.get('studio_format', 'png')
    if not token:
        return JsonResponse(
            {'error': 'Нет обработанного изображения. Сначала нажмите «Обработать».'},
            status=400,
        )

    ext      = {'jpeg': 'jpg', 'png': 'png', 'webp': 'webp'}.get(fmt, 'png')
    tmp_path = f'studio_tmp/{token}.{ext}'
    if not default_storage.exists(tmp_path):
        return JsonResponse(
            {'error': 'Временный файл не найден. Нажмите «Обработать» снова.'},
            status=400,
        )

    with default_storage.open(tmp_path, 'rb') as fh:
        file_bytes = fh.read()

    target = request.POST.get('target', '')

    if target.startswith('product:'):
        slug = target[8:]
        product = get_object_or_404(Product, slug=slug)
        if product.image:
            product.image.delete(save=False)
        product.image.save(f'{slug}.{ext}', ContentFile(file_bytes), save=True)
        return JsonResponse({'ok': True, 'message': f'Изображение сохранено в товар «{product.name}»'})

    if target.startswith('option:'):
        try:
            option_id = int(target[7:])
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Неверный ID опции'}, status=400)
        option = get_object_or_404(
            AttributeOption.objects.select_related('group__product'), id=option_id
        )
        if option.image:
            option.image.delete(save=False)
        option.image.save(f'option-{option_id}.{ext}', ContentFile(file_bytes), save=True)
        return JsonResponse({'ok': True, 'message': f'Изображение сохранено в опцию «{option.name}»'})

    return JsonResponse({'error': 'Укажите цель: товар или опцию'}, status=400)
