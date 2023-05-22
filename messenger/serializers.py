from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Chat, Message, Profile, Group


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class ProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('photo', 'group', 'is_teacher')
        depth = 1


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class ChatSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo', 'type', 'creator')
        depth = 1


class ExtendedChatSerializer(ChatSerializer):
    users = UserSerializer(many=True, read_only=True)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('number', 'chat', 'user', 'text', 'timestamp')


class ExtendedMessageSerializer(MessageSerializer):
    user = UserSerializer(read_only=True)
