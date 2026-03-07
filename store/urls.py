from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),
    path('categoria/<slug:slug>/', views.category_view, name='category'),
    path('producto/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('cuenta/registrarse/', views.register_view, name='register'),
    path('cuenta/ingresar/', views.login_view, name='login'),
    path('cuenta/salir/', views.logout_view, name='logout'),
    path('cuenta/perfil/', views.profile_view, name='profile'),
]
