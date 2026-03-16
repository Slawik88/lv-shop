from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    verbose_name = 'Позиция'
    verbose_name_plural = 'Состав заказа'
    readonly_fields = ('product_name', 'quantity', 'price', 'line_total_display', 'configuration_summary')
    fields = ('product_name', 'quantity', 'price', 'line_total_display', 'configuration_summary')

    def line_total_display(self, obj):
        return f'{obj.line_total} ₽'
    line_total_display.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'customer_name', 'customer_email', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    list_display_links = ('short_id', 'customer_name')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    readonly_fields = ('id', 'total_price', 'created_at', 'updated_at')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    fieldsets = (
        ('Данные покупателя', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address'),
        }),
        ('Заказ', {
            'fields': ('status', 'notes', 'total_price'),
            'description': 'Итоговая сумма пересчитывается автоматически.',
        }),
        ('Служебная информация', {
            'classes': ('collapse',),
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )

    def short_id(self, obj):
        return f'#{str(obj.id)[:8]}'
    short_id.short_description = 'Номер заказа'
    short_id.admin_order_field = 'created_at'
