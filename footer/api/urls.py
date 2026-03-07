from django.urls import path
from . import views

urlpatterns = [
    path('create/',                  views.create_data,          name='footer_create'),
    path('all/',                     views.get_all_data,         name='footer_all'),
    path('<int:id>/',                views.get_by_id,            name='footer_by_id'),
    path('<int:id>/update/',         views.update_data,          name='footer_update'),
    path('<int:id>/image/logo/',     views.delete_logo,          name='footer_delete_logo'),
    path('<int:id>/image/payment/',  views.delete_payment_image, name='footer_delete_payment'),
    path('<int:id>/delete/',         views.delete_data,          name='footer_delete'),
]
