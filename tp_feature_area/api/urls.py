from django.urls import path
from . import views

urlpatterns = [
    path('create/',             views.create_data,  name='tp_feature_area_create'),
    path('all/',                views.get_all_data, name='tp_feature_area_all'),
    path('<int:id>/',           views.get_by_id,    name='tp_feature_area_by_id'),
    path('<int:id>/update/',    views.update_data,  name='tp_feature_area_update'),
    path('<int:id>/delete/',    views.delete_data,  name='tp_feature_area_delete'),
]
