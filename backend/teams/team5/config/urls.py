from core import views
from django.urls import path

urlpatterns = [
    path("health", views.health),
    path("", views.index),
]
