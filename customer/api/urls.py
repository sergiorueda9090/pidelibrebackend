from django.urls import path
from . import views

urlpatterns = [
    # Customer CRUD
    path('create/',                       views.create_data,    name='customer_create'),
    path('all/',                          views.get_all_data,   name='customer_all'),
    path('<int:id>/',                     views.get_by_id,      name='customer_by_id'),
    path('<int:id>/update/',              views.update_data,    name='customer_update'),
    path('<int:id>/delete/',              views.delete_data,    name='customer_delete'),
    # Customer Address CRUD
    path('<int:id>/address/create/',      views.create_address, name='customer_address_create'),
    path('address/<int:id>/update/',      views.update_address, name='customer_address_update'),
    path('address/<int:id>/delete/',      views.delete_address, name='customer_address_delete'),
]
