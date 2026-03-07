from django.contrib import admin
from .models import Category, Product, AttributeGroup, AttributeOption, TextFieldConfig, ProductSize


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------

class AttributeOptionInline(admin.TabularInline):
    model = AttributeOption
    extra = 1
    fields = ('name', 'slug', 'price_modifier', 'image', 'color_hex', 'is_default', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}


class AttributeGroupInline(admin.StackedInline):
    model = AttributeGroup
    extra = 0
    fields = ('name', 'slug', 'widget_type', 'is_required', 'sort_order')
    prepopulated_fields = {'slug': ('name',)}
    show_change_link = True


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1
    fields = ('name', 'width', 'height', 'depth', 'unit', 'price_modifier', 'is_default', 'sort_order')


class TextFieldConfigInline(admin.StackedInline):
    model = TextFieldConfig
    extra = 0
    fieldsets = (
        (None, {
            'fields': ('label', 'placeholder', 'max_length', 'is_required', 'sort_order'),
        }),
        ('Настройки превью', {
            'classes': ('collapse',),
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
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'base_price', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    list_editable = ('base_price', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [ProductSizeInline, AttributeGroupInline, TextFieldConfigInline]

    fieldsets = (
        (None, {
            'fields': ('id', 'category', 'name', 'slug', 'description', 'base_price', 'image'),
        }),
        ('Статус', {
            'fields': ('is_active',),
        }),
        ('Метаданные', {
            'classes': ('collapse',),
            'fields': ('meta', 'created_at', 'updated_at'),
        }),
    )


@admin.register(AttributeGroup)
class AttributeGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'widget_type', 'is_required', 'sort_order')
    list_filter = ('product', 'widget_type')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [AttributeOptionInline]
