from django.urls import path

from registry import views

urlpatterns = [
    path("panel/services", views.PanelServicesView.as_view(), name="panel-services"),
]
