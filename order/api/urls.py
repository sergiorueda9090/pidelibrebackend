from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_order_view, name='order_create'),
    path('all/', views.order_list_view, name='order_list'),
    path('reports/sales/', views.sales_report_view, name='sales_report'),
    path('detail/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('webhooks/mercadopago/', views.webhook_mercadopago, name='webhook_mercadopago'),
]
