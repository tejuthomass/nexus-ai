from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_view, name='chat'),
    path('chat/<int:session_id>/', views.chat_view, name='chat_session'),
    path('new/', views.new_chat, name='new_chat'),
    path('chat/<int:session_id>/delete/', views.delete_user_chat_session, name='delete_user_chat_session'),
    path('chat/<int:session_id>/rename/', views.rename_chat, name='rename_chat'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('dashboard/user/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('dashboard/chat/<int:session_id>/delete/', views.delete_chat_session, name='delete_chat_session'),
    path('dashboard/chat/<int:session_id>/view/', views.view_chat_readonly, name='view_chat_readonly'),
    path('api/admin-chat/<int:session_id>/', views.api_admin_chat, name='api_admin_chat'),
]