import uuid
from django.db import models
from configurator.models import SavedConfiguration


class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтверждён'),
        ('in_production', 'В производстве'),
        ('shipped', 'Отправлен'),
        ('completed', 'Завершён'),
        ('cancelled', 'Отменён'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField('Имя клиента', max_length=300)
    customer_email = models.EmailField('Email')
    customer_phone = models.CharField('Телефон', max_length=20, blank=True)
    customer_address = models.TextField('Адрес доставки', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    notes = models.TextField('Комментарий', blank=True)
    total_price = models.DecimalField('Итоговая сумма', max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{str(self.id)[:8]} — {self.customer_name}'

    def recalculate_total(self):
        self.total_price = sum(item.price * item.quantity for item in self.items.all())
        self.save(update_fields=['total_price'])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items',
                              verbose_name='Заказ')
    configuration = models.ForeignKey(
        SavedConfiguration, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='order_items', verbose_name='Конфигурация',
    )
    product_name = models.CharField('Название товара', max_length=300)
    configuration_summary = models.JSONField('Параметры конфигурации', default=dict)
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product_name} × {self.quantity}'

    @property
    def line_total(self):
        return self.price * self.quantity
