from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Chat, Message, Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('id', 'bio', 'photo', )


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo')


class ExtendedChatSerializer(ChatSerializer):
    users = UserSerializer(many=True, read_only=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('number', 'chat', 'user', 'text', 'timestamp')


class ExtendedMessageSerializer(MessageSerializer):
    user = UserSerializer(read_only=True)
