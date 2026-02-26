from django.urls import path
from . import views

urlpatterns = [
    path('create/',          views.create_data,  name='attribute_create'),
    path('all/',             views.get_all_data, name='attribute_all'),
    path('<int:id>/',        views.get_by_id,    name='attribute_by_id'),
    path('<int:id>/update/', views.update_data,  name='attribute_update'),
    path('<int:id>/delete/', views.delete_data,  name='attribute_delete'),
]
