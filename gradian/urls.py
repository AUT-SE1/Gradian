from django.urls import path, re_path

from core import views

urlpatterns = [
    path("api/auth/me/", views.me),
    path("api/admin-panel/", views.admin_panel),
    *[path(f"api/admin-panel/{f}/", views.feature("admin", f)) for f in views.ADMIN_FEATURES],
    path("api/candidate/", views.candidate_landing),
    re_path(r"^api/teams/(?P<team>\d+)/(?P<path>.*)$", views.team_proxy),
    path("api/advisor/", views.advisor_page),
    *[path(f"api/advisor/{f}/", views.feature("advisor", f)) for f in views.ADVISOR_FEATURES],
]
