from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views
from rest_framework import routers
from django.views.generic import TemplateView

from . import views


router = routers.DefaultRouter()
router.register(r'chats', views.ChatViewSet, basename='chat')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'groups', views.GroupViewSet, basename='group')


urlpatterns = [
    # re_path(r'^rest-auth/google/$', views.GoogleLogin.as_view(), name='google_login'),
    # path('google/', views.GoogleLoginApi.as_view(), name='login-with-google'),

    path('accounts/google/login/callback/', views.GoogleLoginApi.as_view(), name='google_login'),

    path('api/', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/messages_list', views.MessageListAPIView.as_view(), name='messages_list'),


    path(r'test', TemplateView.as_view(template_name='messenger/message.html', extra_context={'username': 'orez', 'timestamp': '1', 'message': '1'}), name='test'),

    path(r'', views.home, name='home'),
    path(r'login/', auth_views.LoginView.as_view(template_name='messenger/login.html', next_page='home'), name='login'),
    path(r'logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path(r'signup/', views.signup, name='signup'),
    path(r'account_activation_sent/', views.account_activation_sent, name='account_activation_sent'),
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$', views.activate,
            name='activate'),
    path('chat/<int:chat_id>/', views.chat, name='chat_content'),
    path('chat/<int:chat_id>/info/', views.chat_info, name='chat_info'),
]
