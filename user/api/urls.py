from django.urls import path
from . import views

urlpatterns = [
    path('me/',                 views.me,               name='me'),
    path('create/',             views.create_data,      name='create_data'),
    path('all/',                views.get_all_data,     name='get_all_data'),
    path('<int:id>/',           views.get_by_id,        name='get_by_id'),
    path('<int:id>/update/',    views.update_data,      name='update_data'),
    path('<int:id>/image/',     views.delete_image,     name='delete_image'),
    path('<int:id>/delete/',    views.delete_data,      name='delete_data'),
]