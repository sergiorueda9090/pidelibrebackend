from django.urls import path
from . import views

urlpatterns = [
    path('create/',             views.create_data,  name='brand_create'),
    path('all/',                views.get_all_data, name='brand_all'),
    path('<int:id>/',           views.get_by_id,    name='brand_by_id'),
    path('<int:id>/update/',    views.update_data,  name='brand_update'),
    path('<int:id>/logo/',      views.delete_logo,  name='brand_delete_logo'),
    path('<int:id>/delete/',    views.delete_data,  name='brand_delete'),
]
