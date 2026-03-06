from django.urls import path
from . import views

urlpatterns = [
    path('create/',             views.create_data,  name='gender_create'),
    path('all/',                views.get_all_data, name='gender_all'),
    path('<int:id>/',           views.get_by_id,    name='gender_by_id'),
    path('<int:id>/update/',    views.update_data,  name='gender_update'),
    path('<int:id>/delete/',    views.delete_data,  name='gender_delete'),
]
