from django.urls import path

from panels import views

urlpatterns = [
    path("landing", views.LandingView.as_view(), name="landing"),
    path("panel", views.PanelView.as_view(), name="panel"),
    path("student/dashboard", views.StudentDashboardView.as_view(), name="student-dashboard"),
    path("notifications", views.NotificationListView.as_view(), name="notifications"),
]
