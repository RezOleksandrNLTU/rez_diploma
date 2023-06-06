from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Chat, Message, Profile, Group


message_timestamp_format = '%Y-%d-%m %H:%M:%S'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class ProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('photo', 'group', 'is_teacher')
        depth = 1


class MessageProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ('photo',)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class ReadonlyUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class MessageUserSerializer(serializers.ModelSerializer):
    profile = MessageProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'profile')


class ChatSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()

    def get_last_message(self, obj):
        try:
            return ChatListMessageSerializer(Message.objects.filter(chat=obj).order_by('-number')[0]).data
        except IndexError:
            return None

    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo', 'type', 'creator', 'group', 'last_message')
        read_only_fields = ('id', 'type', 'creator', 'group', 'last_message')


class DetailedChatSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    creator = ReadonlyUserSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo', 'type', 'creator', 'group')
        read_only_fields = ('id', 'type', 'creator', 'group')
        depth = 1


class CreateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo', 'type', 'creator', 'group')
        read_only_fields = ('id', 'creator', 'group')


class UpdateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('id', 'name', 'users', 'photo', 'type', 'creator', 'group')
        read_only_fields = ('id', 'type', 'creator', 'group', 'users')


class ExtendedChatSerializer(ChatSerializer):
    users = UserSerializer(many=True, read_only=True)


class MessageSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format=message_timestamp_format)
    user = MessageUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('number', 'chat', 'user', 'text', 'file', 'timestamp')


class ChatListMessageSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format=message_timestamp_format)
    user = MessageUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('user', 'text', 'file', 'timestamp')
        depth = 1
