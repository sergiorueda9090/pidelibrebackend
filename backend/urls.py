"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView)

urlpatterns = [
    path('', include('store.urls')),
    path('admin/', admin.site.urls),
    path('api/token/',              TokenObtainPairView.as_view(),  name='token_obtain_pair'),
    path('api/token/refresh/',      TokenRefreshView.as_view(),     name='token_refresh'),
    path('api/user/',               include('user.api.urls') , name='user_api'),
    path('api/category/',           include('category.api.urls'), name='category_api'),
    path('api/attribute/',          include('attribute.api.urls'), name='attribute_api'),
    path('api/attribute-value/',    include('attribute_value.api.urls'), name='attribute_value_api'),
    path('api/product/',            include('product.api.urls'), name='product_api'),
    path('api/brand/',              include('brand.api.urls'), name='brand_api'),
    path('api/gender/',             include('gender.api.urls'), name='gender_api'),
    path('api/customer/',           include('customer.api.urls'), name='customer_api'),
    path('api/slider/',             include('slider.api.urls'), name='slider_api'),
    path('api/tp-feature-area/',    include('tp_feature_area.api.urls'), name='tp_feature_area_api'),
    path('api/footer/',             include('footer.api.urls'), name='footer_api'),
    path('api/',                     include('departamento_municipio.urls')),
    path('api/order/',               include('order.api.urls'), name='order_api'),
]

handler404 = 'store.views.custom_404'

if not settings.DEBUG:
    import re
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]
