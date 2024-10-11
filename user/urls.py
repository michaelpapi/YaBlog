"""Defines URL patterns for user."""

from django.urls import path, include
from . import views

app_name='user'
urlpatterns = [
    # Include default auth urls.
    path('', include('django.contrib.auth.urls')),

     # Confirming logout page
    path('confirm_logout/', views.confirm_logout, name="confirm_logout"),

    # Registration page
    path('register/', views.register, name="register"), 

    
]