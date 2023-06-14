from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Chat, Message, Profile, Group, DocumentTemplate


message_timestamp_format = '%Y-%d-%m %H:%M:%S'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


class DetailedGroupSerializer(serializers.ModelSerializer):
    degree = serializers.CharField(source='get_degree')

    class Meta:
        model = Group
        fields = ('id', 'name', 'study_year', 'speciality', 'institute', 'faculty', 'degree')


class ProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('photo', 'group', 'is_teacher')
        depth = 1


class EditProfileSerializer(serializers.ModelSerializer):
    group = GroupSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('photo', 'group', 'is_teacher', 'patronymic', 'diploma_topic', 'diploma_supervisor_1',
                  'diploma_supervisor_2', 'diploma_reviewer')
        read_only_fields = ('group', 'is_teacher')
        depth = 1


class DetailedProfileSerializer(serializers.ModelSerializer):
    group = DetailedGroupSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ('photo', 'group', 'is_teacher', 'patronymic', 'diploma_topic', 'diploma_supervisor_1',
                  'diploma_supervisor_2', 'diploma_reviewer')
        read_only_fields = ('photo', 'group', 'is_teacher', 'patronymic', 'diploma_topic', 'diploma_supervisor_1',
                            'diploma_supervisor_2', 'diploma_reviewer')
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


class EditUserSerializer(serializers.ModelSerializer):
    profile = EditProfileSerializer()

    def update(self, instance, validated_data):
        if self.partial:
            if 'profile' in validated_data:
                profile_data = validated_data.pop('profile')
                profile = instance.profile
                for key, value in profile_data.items():
                    setattr(profile, key, value)
                profile.save()

            if 'first_name' in validated_data:
                instance.first_name = validated_data.pop('first_name')

            if 'last_name' in validated_data:
                instance.last_name = validated_data.pop('last_name')

            instance.save()

        return instance

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id', 'username', 'email')


class DetailedUserSerializer(serializers.ModelSerializer):
    profile = DetailedProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')
        read_only_fields = ('id', 'username', 'email', 'first_name', 'last_name', 'profile')


class MinimumUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name')


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
    users = MinimumUserSerializer(many=True, read_only=True)

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
        fields = ('id', 'number', 'chat', 'user', 'text', 'file', 'timestamp', 'pinned')


class ChatListMessageSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(format=message_timestamp_format)
    user = MessageUserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ('user', 'text', 'file', 'timestamp', 'pinned')
        depth = 1


class DocumentTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentTemplate
        fields = ('name', 'button_text')
        read_only_fields = ('name', 'button_text')
