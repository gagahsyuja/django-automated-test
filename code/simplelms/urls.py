"""
URL configuration for simplelms project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from lms_core.views import index, testing, addData, editData, deleteData
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from lms_core.api import router
from ninja import NinjaAPI
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication


api = NinjaAPI()
api.add_router("", router)

urlpatterns = [
    path('api/v1/', api.urls),
    path('admin/', admin.site.urls),
    path('testing/', testing),
    path('tambah/', addData),
    path('ubah/', editData),
    path('hapus/', deleteData),
    path('', index),
]
