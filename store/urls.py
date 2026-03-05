from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('categoria/<slug:slug>/', views.category_view, name='category'),
    path('producto/<slug:slug>/', views.product_detail_view, name='product_detail'),
]
