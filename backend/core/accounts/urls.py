from django.urls import path

from accounts import internal_views, user_views, views

urlpatterns = [
    path("auth/config", views.AuthConfigView.as_view(), name="auth-config"),
    path("me", views.MeView.as_view(), name="me"),
    path("admin/users", user_views.UserListCreateView.as_view(), name="admin-users"),
    path("admin/users/<uuid:sub>", user_views.UserDetailView.as_view(), name="admin-user"),
    path("internal/users", internal_views.InternalUserListView.as_view(), name="internal-users"),
    path(
        "internal/users/<uuid:sub>", internal_views.InternalUserView.as_view(), name="internal-user"
    ),
]
