from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from rest_framework import routers

from . import views
from . import api


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'chats', api.ChatViewSet, basename='chat')
router.register(r'messages', api.MessageViewSet, basename='message')
router.register(r'users', api.UserViewSet, basename='user')


urlpatterns = [
    path('accounts/google/login/callback/', api.google_login_callback, name='google_login_callback'),
    path('api/', include(router.urls)),

    path(r'', views.home, name='home'),
    path(r'login', auth_views.LoginView.as_view(template_name='messenger/login.html', next_page='home'), name='login'),
    path(r'logout', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path(r'signup', views.signup, name='signup'),
    path(r'account_activation_sent', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})$', views.activate,
            name='activate'),
    path('chat/<int:chat_id>', views.chat, name='chat_content'),
    path('chat/<int:chat_id>/info', views.chat_info, name='chat_info'),
]
