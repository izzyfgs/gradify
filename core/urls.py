from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    # Add this line here:
    path("register/", views.register_view, name="register"), 
    
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    # ... rest of your URLs

    path("setup-subjects/", views.setup_subjects_view, name="setup_subjects"),
    path("add-score/", views.add_score_view, name="add_score"),
    path("view-scores/", views.view_scores_view, name="view_scores"),

    # ✅ NEW
    path("score/<int:score_id>/edit/", views.edit_score_view, name="edit_score"),
    path("score/<int:score_id>/delete/", views.delete_score_view, name="delete_score"),

    path("help-support/", views.help_support_view, name="help_support"),
    path("support-chat/", views.support_chat_api, name="support_chat"),

    # ✅ NEW: separate AI chat page
    path("ai-chat/", views.ai_chat_view, name="ai_chat"),

    # ✅ AI Chat (separate page)
    path("ai-chat/", views.ai_chat_view, name="ai_chat"),
    path("ai-chat/send/", views.ai_chat_send, name="ai_chat_send"),
    path("ai-chat/clear/", views.ai_chat_clear, name="ai_chat_clear"),

]
