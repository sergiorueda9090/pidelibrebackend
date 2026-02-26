from django.urls import path
from . import views

urlpatterns = [
    path('create/',             views.create_data,  name='category_create'),
    path('all/',                views.get_all_data, name='category_all'),
    path('<int:id>/',           views.get_by_id,    name='category_by_id'),
    path('<int:id>/update/',    views.update_data,  name='category_update'),
    path('<int:id>/image/',     views.delete_image, name='category_delete_image'),
    path('<int:id>/delete/',    views.delete_data,  name='category_delete'),
]
