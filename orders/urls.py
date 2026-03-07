from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:index>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:index>/', views.update_cart_quantity, name='update_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('pdf/<uuid:order_id>/', views.order_pdf, name='order_pdf'),
]
