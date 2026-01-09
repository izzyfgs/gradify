from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard_view, name="dashboard"),

    path("setup-subjects/", views.setup_subjects_view, name="setup_subjects"),
    path("add-score/", views.add_score_view, name="add_score"),
    path("view-scores/", views.view_scores_view, name="view_scores"),

    path("help-support/", views.help_support_view, name="help_support"),
]
