from django.contrib import admin
from .models import Category, Product, AttributeGroup, AttributeOption, TextFieldConfig, ProductSize


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1
    verbose_name = 'Опция'
    verbose_name_plural = 'Опции этой группы'
    fields = ('name', 'slug', 'price_modifier', 'image', 'color_hex', 'is_default', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}


class AttributeGroupInline(admin.StackedInline):
    model = AttributeGroup
    extra = 0
    verbose_name = 'Группа атрибутов'
    verbose_name_plural = 'Группы атрибутов (Материал, Цвет, Шрифт …)'
    fields = ('name', 'slug', 'widget_type', 'is_required', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    verbose_name = 'Размер'
    verbose_name_plural = 'Размеры изделия'
    fields = ('name', 'width', 'height', 'depth', 'unit', 'price_modifier', 'is_default', 'sort_order')


class TextFieldConfigInline(admin.StackedInline):
    model = TextFieldConfig
    extra = 0
    verbose_name = 'Текстовое поле'
    verbose_name_plural = 'Текстовые поля (ФИО, Должность …)'
    fieldsets = (
        (None, {
            'fields': ('label', 'placeholder', 'max_length', 'is_required', 'sort_order'),
        }),
        ('Позиция и шрифт на превью', {
            'classes': ('collapse',),
            'description': 'Координаты X/Y задаются в пикселях относительно левого верхнего угла изображения.',
            'fields': (
                ('preview_x', 'preview_y'),
                ('preview_font_size', 'preview_font_family'),
                ('preview_color', 'preview_text_anchor'),
                'preview_max_width',
            ),
        }),
    )


# ---------------------------------------------------------------------------
# Admin classes
# ---------------------------------------------------------------------------

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order', 'is_active')
    list_editable = ('sort_order', 'is_active')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'description', 'image'),
        }),
        ('Настройки отображения', {
            'fields': ('sort_order', 'is_active'),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    list_editable = ('base_price', 'is_active')
    list_display_links = ('name',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ProductSizeInline, AttributeGroupInline, TextFieldConfigInline]

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'category', 'name', 'slug', 'description', 'base_price', 'image'),
        }),
        ('Публикация', {
            'fields': ('is_active',),
            'description': 'Неактивные товары не отображаются на сайте.',
        }),
        ('Служебные данные', {
            'classes': ('collapse',),
            'fields': ('meta', 'created_at', 'updated_at'),
        }),
    )


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'widget_type', 'is_required', 'sort_order')
    list_filter = ('product', 'widget_type')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AttributeOptionInline]
    fieldsets = (
        ('Группа атрибутов', {
            'description': 'Группа объединяет однотипные опции товара (например, все варианты материала).',
            'fields': ('product', 'name', 'slug', 'widget_type', 'is_required', 'sort_order'),
        }),
    )
