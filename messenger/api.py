import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import redirect
from django.contrib.auth import login
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import authentication_classes, permission_classes

from . import serializers as msg_serializers
from .models import Chat, Message, Group, Profile, User
from msg.settings import BASE_FRONTEND_URL


@authentication_classes([])
@permission_classes([])
class GoogleLoginApi(APIView):
    GOOGLE_ID_TOKEN_INFO_URL = 'https://www.googleapis.com/oauth2/v3/tokeninfo'
    GOOGLE_ACCESS_TOKEN_OBTAIN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'

    class InputSerializer(serializers.Serializer):
        code = serializers.CharField(required=False)
        error = serializers.CharField(required=False)

    def google_get_access_token(self, *, code: str, redirect_uri: str) -> str:
        data = {
            'grant_type': 'authorization_code',
            'client_id': '163959136765-5qj37lcjnv2g8hci1sjksr5nvj1jnlqj.apps.googleusercontent.com',
            'client_secret': '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',
            'redirect_uri': redirect_uri,
            'code': code,
        }
        response = requests.post(self.GOOGLE_ACCESS_TOKEN_OBTAIN_URL, data=data)
        if not response.ok:
            raise ValidationError('Failed to obtain access token from Google.')
        access_token = response.json()['access_token']
        return access_token

    def google_get_user_info(self, *, access_token: str):
        response = requests.get(
            self.GOOGLE_USER_INFO_URL,
            params={'access_token': access_token}
        )

        if not response.ok:
            raise ValidationError('Failed to obtain user info from Google.')

        return response.json()

    def get(self, request, *args, **kwargs):
        input_serializer = self.InputSerializer(data=request.GET)
        input_serializer.is_valid(raise_exception=True)
        validated_data = input_serializer.validated_data
        code = validated_data.get('code')
        error = validated_data.get('error')
        login_url = f'{BASE_FRONTEND_URL}/login?error={error}'

        if error or not code:
            return redirect(login_url)
        redirect_uri = f'http://localhost:8000/accounts/google/login/callback/'

        access_token = self.google_get_access_token(code=code, redirect_uri=redirect_uri)

        user_data = self.google_get_user_info(access_token=access_token)

        profile_data = {
            'email': user_data['email'],
            'first_name': user_data.get('givenName', ''),
            'last_name': user_data.get('familyName', ''),
        }

        user, created = User.objects.get_or_create(
            email=profile_data['email'],
            defaults=profile_data
        )

        if not created:
            user.first_name = profile_data['first_name']
            user.last_name = profile_data['last_name']
            user.save()

        picture_url = user_data.get('picture', '')
        if picture_url:
            user.profile.get_photo_from_url(picture_url)

        response = redirect(BASE_FRONTEND_URL)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        response.set_cookie('user_id', user.id)
        return response


google_login_callback = GoogleLoginApi.as_view()


class ChatViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'head', 'options', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Chat.objects.filter(users=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return msg_serializers.DetailedChatSerializer
        elif self.action == 'create':
            return msg_serializers.CreateChatSerializer
        elif self.action == 'list':
            return msg_serializers.ChatSerializer
        elif self.action in ['update', 'partial_update']:
            return msg_serializers.UpdateChatSerializer
        return msg_serializers.ChatSerializer

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.type == Chat.CHAT_TYPES[0][0]:
            return Response({'error': 'You are not allowed to edit this chat.'}, status=403)
        if instance.type == Chat.CHAT_TYPES[2][0] and not request.user.profile.is_teacher:
            return Response({'error': 'You are not allowed to edit this chat.'}, status=403)
        if request.user != instance.creator:
            return Response({'error': 'You are not allowed to edit this chat.'}, status=403)
        return super().partial_update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if request.data.get('type') == Chat.CHAT_TYPES[0][0]:
            users = request.data.get('users', [])
            if len(users) != 2 and request.user not in users:
                return Response({'error': 'You are not allowed to create this chat.'}, status=403)
            try:
                Chat.objects.get(users__in=users, type=Chat.CHAT_TYPES[0][0])
            except Chat.DoesNotExist:
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                self.perform_create(serializer)
                return Response(serializer.data, status=201)
            else:
                return Response({'error': 'This chat already exists'}, status=403)
        elif request.data.get('type') == Chat.CHAT_TYPES[1][0]:
            return super().create(request, *args, **kwargs)
        elif request.data.get('type') == Chat.CHAT_TYPES[2][0]:
            return Response({'error': 'You are not allowed to create this chat.'}, status=403)
        return Response({'error': 'You are not allowed to create this chat.'}, status=403)

    def perform_create(self, serializer):
        if serializer.validated_data.get('type') == Chat.CHAT_TYPES[1][0]:
            serializer.save(creator=self.request.user)
        else:
            serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.type == Chat.CHAT_TYPES[0][0]:
            return Response({'error': 'You are not allowed to delete this chat.'}, status=403)
        if instance.type == Chat.CHAT_TYPES[2][0] and not request.user.profile.is_teacher:
            return Response({'error': 'You are not allowed to delete this chat.'}, status=403)
        if request.user != instance.creator:
            return Response({'error': 'You are not allowed to delete this chat.'}, status=403)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def leave_chat(self, request, *args, **kwargs):
        sender = request.user
        instance = self.get_object()
        if instance.type == Chat.CHAT_TYPES[0][0]:
            return Response({'error': 'You are not allowed to leave this chat.'}, status=403)
        if instance.type == Chat.CHAT_TYPES[2][0] and not request.user.profile.is_teacher:
            return Response({'error': 'You are not allowed to leave this chat.'}, status=403)
        if sender == instance.creator:
            return Response({'error': 'You are not allowed to leave this chat.'}, status=403)
        instance.users.remove(sender)
        instance.save()
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def add_users(self, request, *args, **kwargs):
        sender = request.user
        instance = self.get_object()

        if instance.type == Chat.CHAT_TYPES[0][0]:
            return Response({'error': 'You are not allowed to add users to this chat.'}, status=403)
        if instance.type == Chat.CHAT_TYPES[2][0] and not request.user.profile.is_teacher:
            return Response({'error': 'You are not allowed to add users to this chat.'}, status=403)
        if sender != instance.creator:
            return Response({'error': 'You are not allowed to add users to this chat.'}, status=403)

        users = request.data.get('users', [])

        for user_id in users:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                continue
            if user not in instance.users.all():
                instance.users.add(user)
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def remove_users(self, request, *args, **kwargs):
        sender = request.user
        instance = self.get_object()

        if instance.type == Chat.CHAT_TYPES[0][0]:
            return Response({'error': 'You are not allowed to remove users from this chat.'}, status=403)
        if instance.type == Chat.CHAT_TYPES[2][0] and not request.user.profile.is_teacher:
            return Response({'error': 'You are not allowed to remove users from this chat.'}, status=403)
        if sender != instance.creator:
            return Response({'error': 'You are not allowed to remove users from this chat.'}, status=403)

        users = request.data.getlist('users', [])

        if str(sender.id) in users:
            return Response({'error': 'You are not allowed to remove yourself from this chat.'}, status=403)

        for user_id in users:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                continue
            if user in instance.users.all():
                instance.users.remove(user)
        return Response({'status': 'ok'})


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = msg_serializers.MessageSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'head', 'options']

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
        except ValidationError as e:
            return Response({'error': e.detail[0]}, status=e.status_code)

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        return Response({'error': 'Method not allowed.'}, status=405)

    def create(self, request, *args, **kwargs):
        chat_id = request.data.get('chat_id')

        if not chat_id:
            return Response({'error': 'Chat id is required.'}, status=400)

        try:
            chat = Chat.objects.get(id=chat_id)
        except Chat.DoesNotExist:
            return Response({'error': 'This chat does not exist.'}, status=404)

        if not chat.is_user_in_chat(request.user):
            return Response({'error': 'You are not allowed to send messages to this chat.'}, status=403)

        text = request.data.get('text')
        file = request.data.get('file')

        if not text and not file:
            return Response({'error': 'Message text or file is required.'}, status=400)

        if text and file:
            return Response({'error': 'Message text and file are mutually exclusive.'}, status=400)

        if text:
            message = Message.objects.create(text=text, user=request.user, chat=chat)
        else:
            message = Message.objects.create(file=file, user=request.user, chat=chat)

        channel_layer = get_channel_layer()
        group_name = f'chat_{chat.id}'
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'chat_message',
                'message': msg_serializers.MessageSerializer(message).data
            }
        )

        serializer = self.get_serializer(message)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

    def get_queryset(self):
        chat_id = self.request.query_params.get('chat_id')

        if not chat_id:
            raise ValidationError(detail='chat_id is required.', code=400)

        message_chat = Chat.objects.filter(id=chat_id).first()

        if not message_chat:
            raise ValidationError(detail='This chat does not exist.', code=404)

        if not message_chat.is_user_in_chat(self.request.user):
            raise ValidationError(detail='You are not allowed to see this chat.', code=403)
        starting_number = self.request.query_params.get('starting_number')

        queryset = Message.objects.filter(chat=message_chat)

        if starting_number is not None:
            queryset = queryset.filter(number__lte=starting_number)
        return queryset.order_by('-number')


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = msg_serializers.UserSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'head', 'options', 'post']

    @action(detail=False, methods=['post'], name='Change group')
    def change_group(self, request):
        if 'code' not in request.data:
            return Response({'error': 'Invalid data'}, status=400)
        code = request.data['code']
        try:
            group = Group.objects.get(code=code)
        except Group.DoesNotExist:
            return Response({'error': 'Invalid code'}, status=400)

        try:
            group_chat = Chat.objects.get(type=Chat.CHAT_TYPES[2][0], group=group)
        except Chat.DoesNotExist:
            group_chat = Chat.objects.create(name=f'Дипломний чат {group.name}', type=Chat.CHAT_TYPES[2][0],
                                             group=group)
            group_users = Profile.objects.filter(group=group)
            for user in group_users:
                group_chat.users.add(user.user)
            group_chat.save()

        group_chat.users.add(request.user)

        user = request.user
        user.profile.group = group
        user.save()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
