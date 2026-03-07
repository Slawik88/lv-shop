import uuid
from django.db import models
from products.models import Product


class ConfiguratorTemplate(models.Model):
    """
    Visual template for the product configurator.
    Attached 1-to-1 to a Product. All rendering settings come from DB — ZERO HARDCODE.
    """
    product = models.OneToOneField(
        Product, on_delete=models.CASCADE, related_name='configurator_template',
        verbose_name='Товар',
    )
    base_image = models.ImageField(
        'Базовое изображение', upload_to='templates/base/', blank=True,
        help_text='Чистое фоновое изображение товара (табличка без текста). '
                  'Если не задано — используется фото товара.',
    )
    overlay_mask = models.ImageField(
        'Маска наложения', upload_to='templates/masks/', blank=True,
        help_text='PNG-маска для наложения текстур/материалов',
    )
    width = models.PositiveIntegerField('Ширина SVG (px)', default=600)
    height = models.PositiveIntegerField('Высота SVG (px)', default=400)

    # JSON layer configuration — fully flexible
    layers_config = models.JSONField(
        'Конфигурация слоёв', default=dict, blank=True,
        help_text='''JSON с настройками: {
  "background_color": "#ffffff",
  "border_radius": 10,
  "overlay_opacity": 0.8,
  "extra_decorations": [
    {"type": "line", "x1": 0, "y1": 50, "x2": 600, "y2": 50, "stroke": "#ccc"}
  ]
}''',
    )

    class Meta:
        verbose_name = 'Шаблон конфигуратора'
        verbose_name_plural = 'Шаблоны конфигуратора'

    def __str__(self):
        return f'Шаблон: {self.product.name}'


class FontChoice(models.Model):
    """Available font for preview rendering. Admin adds fonts here."""
    name = models.CharField('Название шрифта', max_length=200, unique=True)
    css_family = models.CharField('CSS font-family', max_length=200,
                                  help_text='Как шрифт называется в CSS')
    font_file = models.FileField('Файл шрифта (.ttf/.woff2)', upload_to='fonts/', blank=True)
    is_active = models.BooleanField('Активен', default=True)
    sort_order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        verbose_name = 'Шрифт'
        verbose_name_plural = 'Шрифты'
        ordering = ['sort_order', 'name']

    def __str__(self):
        return self.name


class SavedConfiguration(models.Model):
    """
    A saved product configuration — snapshot of all user choices.
    Used for cart items and orders.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='saved_configs',
        verbose_name='Товар',
    )
    configuration = models.JSONField(
        'Конфигурация', default=dict,
        help_text='''{
  "options": {"material": "brass", "color": "gold"},
  "texts": {"name": "Иванов И.И.", "title": "Директор"},
  "font": "Arial"
}''',
    )
    calculated_price = models.DecimalField('Рассчитанная цена', max_digits=10, decimal_places=2)
    preview_image = models.ImageField('Превью', upload_to='previews/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сохранённая конфигурация'
        verbose_name_plural = 'Сохранённые конфигурации'
        ordering = ['-created_at']

    def __str__(self):
        return f'Config #{str(self.id)[:8]} — {self.product.name}'
