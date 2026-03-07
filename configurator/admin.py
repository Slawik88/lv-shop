from django.contrib import admin
from .models import ConfiguratorTemplate, FontChoice, SavedConfiguration
from products.models import Product


@admin.register(ConfiguratorTemplate)
class ConfiguratorTemplateAdmin(admin.ModelAdmin):
    list_display = ('product', 'width', 'height')
    list_filter = ('product__category',)
    fieldsets = (
        (None, {
            'fields': ('product', 'base_image', 'overlay_mask'),
        }),
        ('Размеры', {
            'fields': (('width', 'height'),),
        }),
        ('Конфигурация слоёв (JSON)', {
            'classes': ('collapse',),
            'fields': ('layers_config',),
        }),
    )


@admin.register(FontChoice)
class FontChoiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'css_family', 'is_active', 'sort_order')
    list_editable = ('is_active', 'sort_order')
    search_fields = ('name', 'css_family')


@admin.register(SavedConfiguration)
class SavedConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'calculated_price', 'created_at')
    list_filter = ('product',)
    readonly_fields = ('id', 'configuration', 'preview_image', 'created_at')
