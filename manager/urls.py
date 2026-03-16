from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    # Auth
    path('login/',  views.manager_login,  name='login'),
    path('logout/', views.manager_logout, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Products
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<slug:slug>/edit/', views.product_edit, name='product_edit'),
    path('products/<slug:slug>/delete/', views.product_delete, name='product_delete'),

    # Product options (attribute groups, text fields, sizes)
    path('products/<slug:slug>/options/', views.product_options, name='product_options'),

    # Attribute groups
    path('products/<slug:slug>/groups/new/', views.attribute_group_create, name='attribute_group_create'),
    path('products/<slug:slug>/groups/<int:group_id>/edit/', views.attribute_group_edit, name='attribute_group_edit'),
    path('products/<slug:slug>/groups/<int:group_id>/delete/', views.attribute_group_delete, name='attribute_group_delete'),

    # Attribute options
    path('products/<slug:slug>/groups/<int:group_id>/options/new/', views.attribute_option_create, name='attribute_option_create'),
    path('products/<slug:slug>/groups/<int:group_id>/options/<int:option_id>/edit/', views.attribute_option_edit, name='attribute_option_edit'),
    path('products/<slug:slug>/groups/<int:group_id>/options/<int:option_id>/delete/', views.attribute_option_delete, name='attribute_option_delete'),

    # Text fields
    path('products/<slug:slug>/textfields/new/', views.text_field_create, name='text_field_create'),
    path('products/<slug:slug>/textfields/<int:tf_id>/edit/', views.text_field_edit, name='text_field_edit'),
    path('products/<slug:slug>/textfields/<int:tf_id>/delete/', views.text_field_delete, name='text_field_delete'),

    # Sizes
    path('products/<slug:slug>/sizes/new/', views.size_create, name='size_create'),
    path('products/<slug:slug>/sizes/<int:size_id>/edit/', views.size_edit, name='size_edit'),
    path('products/<slug:slug>/sizes/<int:size_id>/delete/', views.size_delete, name='size_delete'),

    # Orders
    path('orders/', views.order_list, name='order_list'),
    path('orders/<uuid:pk>/', views.order_detail, name='order_detail'),

    # Image Studio
    path('image-studio/', views.image_studio, name='image_studio'),
    path('image-studio/process/', views.image_studio_process, name='image_studio_process'),
    path('image-studio/apply/', views.image_studio_apply, name='image_studio_apply'),
]
