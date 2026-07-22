from django.urls import path
from . import views as authentication_views

urlpatterns = [
    path("register/", authentication_views.register, name='authentication-register')
]