from django.urls import path
from . import views

urlpatterns = [
    path('create/',             views.create_data,  name='slider_create'),
    path('all/',                views.get_all_data, name='slider_all'),
    path('<int:id>/',           views.get_by_id,    name='slider_by_id'),
    path('<int:id>/update/',    views.update_data,  name='slider_update'),
    path('<int:id>/image/',     views.delete_image, name='slider_delete_image'),
    path('<int:id>/delete/',    views.delete_data,  name='slider_delete'),
]
