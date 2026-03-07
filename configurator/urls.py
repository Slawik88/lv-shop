from django.urls import path
from . import views

app_name = 'configurator'

urlpatterns = [
    path('preview/<slug:product_slug>.svg', views.preview_svg, name='preview_svg'),
    path('price/<slug:product_slug>/', views.calculate_price, name='calculate_price'),
    path('fonts/', views.get_fonts, name='get_fonts'),
    path('save/<slug:product_slug>/', views.save_configuration, name='save_configuration'),
]
