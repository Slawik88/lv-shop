from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('configuration', 'product_name', 'configuration_summary', 'price')
    fields = ('product_name', 'quantity', 'price', 'configuration', 'configuration_summary')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'customer_email', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    readonly_fields = ('id', 'total_price', 'created_at', 'updated_at')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    fieldsets = (
        ('Клиент', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address'),
        }),
        ('Заказ', {
            'fields': ('status', 'notes', 'total_price'),
        }),
        ('Система', {
            'classes': ('collapse',),
            'fields': ('id', 'created_at', 'updated_at'),
        }),
    )
