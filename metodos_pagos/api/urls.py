from django.urls import path
from . import views

urlpatterns = [
    path('create/',                  views.create_data,   name='payment_method_create'),
    path('all/',                     views.get_all_data,  name='payment_method_all'),
    path('<int:id>/',                views.get_by_id,     name='payment_method_by_id'),
    path('<int:id>/update/',         views.update_data,   name='payment_method_update'),
    path('<int:id>/image/logo/',     views.delete_logo,   name='payment_method_delete_logo'),
    path('<int:id>/delete/',         views.delete_data,   name='payment_method_delete'),
]
