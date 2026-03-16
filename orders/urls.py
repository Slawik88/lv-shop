from django.urls import path
from . import views
from . import auth_views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:index>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:index>/', views.update_cart_quantity, name='update_quantity'),
    path('checkout/', views.checkout, name='checkout'),
    path('success/<uuid:order_id>/', views.order_success, name='order_success'),
    path('pdf/<uuid:order_id>/', views.order_pdf, name='order_pdf'),

    # Customer auth
    path('register/', auth_views.customer_register, name='register'),
    path('login/', auth_views.customer_login, name='login'),
    path('logout/', auth_views.customer_logout, name='logout'),
    path('profile/', auth_views.customer_profile, name='profile'),
]
