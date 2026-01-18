# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # ---------- Dashboard & Auth ----------
    path("", views.dashboard_view, name="dashboard"), # Set as root for core
    path("dashboard/", views.dashboard_view, name="dashboard_alt"), 
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),

    # ---------- Profile & Social ----------
    # ---------- Profile & Social ----------
    # 1. Static paths first (Specific)
    path("profile/edit/", views.edit_profile_view, name="edit_profile"),
    path("user-search/", views.user_search, name="user_search"),

    # 2. Dynamic paths second (Generic)
    path("profile/<str:username>/", views.profile_view, name="profile"),
    path("profile/<str:username>/follow-toggle/", views.follow_toggle_view, name="follow_toggle"),

    # ---------- Wallet ----------
    path('wallet/', views.wallet_home, name='wallet'), 
    path("wallet/send/", views.wallet_send, name="wallet_send"),
    path("wallet/history/", views.wallet_history, name="wallet_history"),
    path("wallet/verify/", views.wallet_verify, name="wallet_verify"),
    path("wallet/betting/", views.wallet_betting, name="wallet_betting"),
    path('wallet/set-pin/', views.wallet_set_pin_view, name='wallet_set_pin'),
    path("wallet/search-users/", views.wallet_user_search, name="wallet_user_search"),

    # ---------- Academics ----------
    path("setup-subjects/", views.setup_subjects_view, name="setup_subjects"),
    path("add-score/", views.add_score_view, name="add_score"),
    path("view-scores/", views.view_scores_view, name="view_scores"),
    path("graph/", views.graph_view, name="graph"),
    path("score/<int:score_id>/edit/", views.edit_score_view, name="edit_score"),
    path("score/<int:score_id>/delete/", views.delete_score_view, name="delete_score"),

    # ---------- Social Interactions ----------
    path("posts/create/", views.create_post_view, name="create_post"),
    path("posts/<int:post_id>/like/", views.like_post_view, name="like_post"),
    path("posts/<int:post_id>/comment/", views.comment_post_view, name="comment_post"),
    path("posts/<int:post_id>/edit/", views.edit_post_view, name="edit_post"),

    # ---------- Notifications & AI ----------
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/mark-read/", views.notifications_mark_read_view, name="notifications_mark_read"),
    path("help-support/", views.help_support_view, name="help_support"),
    path('ai-chat/', views.ai_chat_view, name='ai_chat'),
    path('ai-chat/send/', views.ai_chat_send, name='ai_chat_send'),
    path("ai-chat/clear/", views.ai_chat_clear, name="ai_chat_clear"),

    # ---------- Messaging ----------
    path("messages/", views.messages_inbox, name="messages_inbox"),
    path("messages/search/", views.user_search_ajax, name="user_search_ajax"),
    path("messages/start/<str:username>/", views.start_chat, name="start_chat"),
    path("messages/t/<int:conv_id>/", views.chat_thread, name="chat_thread"),
    path("messages/t/<int:conv_id>/send/", views.chat_send_ajax, name="chat_send_ajax"),
    path("messages/t/<int:conv_id>/poll/", views.chat_poll_ajax, name="chat_poll_ajax"),

    # ---------- Settings & Security ----------
    path("settings/", views.settings_view, name="settings"),
    path("settings/delete-account/", views.delete_account_view, name="delete_account"),
    path("settings/export/", views.export_data_view, name="export_data"),
    path("settings/deactivate/", views.deactivate_account_view, name="deactivate_account"),
    # We point this to edit_profile_view instead of a missing function
path("dashboard/avatar/", views.edit_profile_view, name="dashboard_avatar_upload"),


    # ---------- Password flow ----------
    path("password/change/", auth_views.PasswordChangeView.as_view(template_name="password_change.html"), name="password_change"),
    path("password/change/done/", auth_views.PasswordChangeDoneView.as_view(template_name="password_change_done.html"), name="password_change_done"),
]