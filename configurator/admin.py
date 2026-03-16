from django.contrib import admin
from .models import ConfiguratorTemplate, FontChoice, SavedConfiguration
from products.models import Product


@admin.register(ConfiguratorTemplate)
class ConfiguratorTemplateAdmin(admin.ModelAdmin):
    list_display = ('product', 'width', 'height')
    list_filter = ('product__category',)
    list_display_links = ('product',)
    fieldsets = (
        ('Товар и изображения', {
            'description': 'Привяжите шаблон к товару и загрузите фоновое изображение '
                           '(чистая табличка/кубок без текста).',
            'fields': ('product', 'base_image', 'overlay_mask'),
        }),
        ('Размеры холста (в пикселях)', {
            'description': 'Ширина и высота SVG-холста. Рекомендуется сохранять пропорции реального изделия.',
            'fields': (('width', 'height'),),
        }),
        ('Конфигурация слоёв JSON (дополнительно)', {
            'classes': ('collapse',),
            'description': 'Необязательно. Позволяет задать цвет фона, скругление углов '
                           'и дополнительные декоративные элементы (линии, рамки).',
            'fields': ('layers_config',),
        }),
    )


@admin.register(FontChoice)
class FontChoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'css_family', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    list_display_links = ('name',)
    search_fields = ('name', 'css_family')
    fieldsets = (
        ('Шрифт', {
            'description': 'Шрифты используются в конфигураторе при предпросмотре гравировки. '
                           'CSS font-family должно совпадать с именем шрифта в браузере.',
            'fields': ('name', 'css_family', 'font_file', 'is_active', 'sort_order'),
        }),
    )


@admin.register(SavedConfiguration)
class SavedConfigurationAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'product', 'calculated_price', 'created_at')
    list_filter = ('product',)
    list_display_links = ('short_id', 'product')
    readonly_fields = ('id', 'product', 'configuration', 'preview_image', 'created_at')
    fieldsets = (
        ('Сохранённая конфигурация', {
            'description': 'Снимок всех параметров, выбранных покупателем. Только для чтения.',
            'fields': ('id', 'product', 'calculated_price', 'configuration', 'preview_image', 'created_at'),
        }),
    )

    def short_id(self, obj):
        return f'#{str(obj.id)[:8]}'
    short_id.short_description = 'ID конфигурации'
