from django.urls import path
from . import views

urlpatterns = [
    path('departamentos/', views.departamentos_list, name='departamentos_list'),
    path('departamentos/<int:id_departamento>/municipios/', views.municipios_by_departamento, name='municipios_by_departamento'),
]
