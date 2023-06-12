from django.urls import path, include
from rest_framework import routers

from . import api


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'chats', api.ChatViewSet, basename='chat')
router.register(r'messages', api.MessageViewSet, basename='message')
router.register(r'users', api.UserViewSet, basename='user')


urlpatterns = [
    path('accounts/google/login/callback/', api.google_login_callback, name='google_login_callback'),
    path('api/', include(router.urls)),
]
