import uuid
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Product category (e.g., Таблички, Кубки, Розетки)."""
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Slug', max_length=200, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)
    is_active = models.BooleanField('Активна', default=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})


class Product(models.Model):
    """Base product (e.g., «Табличка на дверь», «Кубок спортивный»)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name='products',
        verbose_name='Категория',
    )
    name = models.CharField('Название', max_length=300)
    slug = models.SlugField('Slug', max_length=300, unique=True, blank=True)
    description = models.TextField('Описание', blank=True)
    base_price = models.DecimalField('Базовая цена', max_digits=10, decimal_places=2)
    image = models.ImageField('Основное изображение', upload_to='products/', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)
    meta = models.JSONField('Метаданные', default=dict, blank=True,
                            help_text='Произвольные метаданные (SEO, переводы)')

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def has_configurator(self):
        return hasattr(self, 'configurator_template') and self.configurator_template is not None


class AttributeGroup(models.Model):
    """
    Группа опций товара (Материал, Цвет, Шрифт).
    Полностью настраиваемо из админки — ZERO HARDCODE.
    """
    WIDGET_CHOICES = [
        ('radio', 'Радиокнопки'),
        ('select', 'Выпадающий список'),
        ('color', 'Палитра цветов'),
        ('image', 'Карточки с изображениями'),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='attribute_groups',
        verbose_name='Товар',
    )
    name = models.CharField('Название группы', max_length=200,
                            help_text='Например: Материал, Цвет, Шрифт')
    slug = models.SlugField('Slug', max_length=200, blank=True)
    widget_type = models.CharField('Тип виджета', max_length=20,
                                   choices=WIDGET_CHOICES, default='radio')
    is_required = models.BooleanField('Обязательно', default=True)
    sort_order = models.PositiveIntegerField('Порядок сортировки', default=0)

    class Meta:
        verbose_name = 'Группа атрибутов'
        verbose_name_plural = 'Группы атрибутов'
        ordering = ['sort_order']
        unique_together = ['product', 'slug']

    def __str__(self):
        return f'{self.product.name} → {self.name}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class AttributeOption(models.Model):
    """Одна опция в группе атрибутов (Латунь, Золото, и т.д.)."""
    group = models.ForeignKey(
        AttributeGroup, on_delete=models.CASCADE, related_name='options',
        verbose_name='Группа',
    )
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Slug', max_length=200, blank=True)
    price_modifier = models.DecimalField(
        'Модификатор цены', max_digits=10, decimal_places=2, default=0,
        help_text='Добавляется к базовой цене (может быть отрицательным)',
    )
    image = models.ImageField('Изображение / Текстура', upload_to='options/', blank=True,
                              help_text='Текстура материала, цвет и т.п.')
    color_hex = models.CharField('Цвет (HEX)', max_length=7, blank=True,
                                 help_text='#RRGGBB — для палитры')
    is_default = models.BooleanField('По умолчанию', default=False)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Опция атрибута'
        verbose_name_plural = 'Опции атрибутов'
        ordering = ['sort_order']

    def __str__(self):
        mod = ''
        if self.price_modifier:
            sign = '+' if self.price_modifier > 0 else ''
            mod = f' ({sign}{self.price_modifier})'
        return f'{self.name}{mod}'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class TextFieldConfig(models.Model):
    """
    Настраиваемое текстовое поле (ФИО, Должность, Надпись).
    Координаты и шрифт считываются SVG-рендерером для превью.
    """
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='text_fields',
        verbose_name='Товар',
    )
    label = models.CharField('Название поля', max_length=200,
                             help_text='Например: ФИО, Должность, Надпись')
    placeholder = models.CharField('Подсказка (placeholder)', max_length=300, blank=True)
    max_length = models.PositiveIntegerField('Макс. символов', default=50)
    is_required = models.BooleanField('Обязательно', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    # -- Preview positioning (SVG renderer reads these) --
    preview_x = models.FloatField('X на превью (px)', default=50,
                                  help_text='Координата X центра текста')
    preview_y = models.FloatField('Y на превью (px)', default=50,
                                  help_text='Координата Y центра текста')
    preview_font_size = models.FloatField('Размер шрифта (px)', default=24)
    preview_font_family = models.CharField('Шрифт', max_length=200, default='Arial',
                                           help_text='CSS font-family')
    preview_color = models.CharField('Цвет текста', max_length=7, default='#000000')
    preview_max_width = models.FloatField('Макс. ширина текста (px)', default=300,
                                          help_text='Текст сожмётся если превысит')
    preview_text_anchor = models.CharField(
        'Выравнивание', max_length=10, default='middle',
        choices=[('start', 'Слева'), ('middle', 'По центру'), ('end', 'Справа')],
    )

    class Meta:
        verbose_name = 'Текстовое поле'
        verbose_name_plural = 'Текстовые поля'
        ordering = ['sort_order']

    def __str__(self):
        return f'{self.product.name} → {self.label}'


class ProductSize(models.Model):
    """
    Размеры изделия, настраиваемые из Admin.
    Отображаются в виде сетки на странице товара.
    """
    UNIT_CHOICES = [
        ('mm', 'мм'),
        ('cm', 'см'),
        ('m', 'м'),
    ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='sizes',
        verbose_name='Товар',
    )
    name = models.CharField('Название', max_length=100,
                            help_text='Например: A4, Стандарт, Большой')
    width = models.DecimalField('Ширина', max_digits=8, decimal_places=1)
    height = models.DecimalField('Высота', max_digits=8, decimal_places=1)
    depth = models.DecimalField('Глубина/Толщина', max_digits=8, decimal_places=1,
                                default=0, blank=True,
                                help_text='0 — если плоское изделие')
    unit = models.CharField('Единицы', max_length=5, choices=UNIT_CHOICES, default='mm')
    price_modifier = models.DecimalField(
        'Модификатор цены', max_digits=10, decimal_places=2, default=0,
        help_text='Добавляется к базовой цене (может быть отрицательным)',
    )
    is_default = models.BooleanField('По умолчанию', default=False)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Размер изделия'
        verbose_name_plural = 'Размеры изделий'
        ordering = ['sort_order', 'width']

    def __str__(self):
        depth_str = f'×{self._fmt(self.depth)}' if self.depth else ''
        mod = ''
        if self.price_modifier:
            sign = '+' if self.price_modifier > 0 else ''
            mod = f' ({sign}{self.price_modifier} ₽)'
        return f'{self.name}: {self._fmt(self.width)}×{self._fmt(self.height)}{depth_str} {self.unit}{mod}'

    @staticmethod
    def _fmt(value) -> str:
        """Format decimal: strip trailing zeros (e.g. 148.0 → 148, 14.5 → 14.5)."""
        return str(value).rstrip('0').rstrip('.')

    @property
    def dimensions_display(self):
        """Human-readable dimension string."""
        f = self._fmt
        if self.depth:
            return f'{f(self.width)}×{f(self.height)}×{f(self.depth)} {self.unit}'
        return f'{f(self.width)}×{f(self.height)} {self.unit}'
