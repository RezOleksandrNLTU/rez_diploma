import requests
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .forms import SignUpForm
from .tokens import account_activation_token
from .models import Chat, Message, Group
from .serializers import ChatSerializer, MessageSerializer, UserSerializer, ExtendedMessageSerializer, \
    ExtendedChatSerializer, GroupSerializer

from rest_framework.decorators import authentication_classes, permission_classes

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
        # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#obtainingaccesstokens
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
        # Reference: https://developers.google.com/identity/protocols/oauth2/web-server#callinganapi
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
        login_url = f'http://localhost:8000/login'
        if error or not code:
            return Response({'login_url': login_url}, 400)
            # return redirect(login_url)
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

        response = redirect('home')
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return response

@login_required(login_url='/login/')
def home(request):
    queryset = Chat.objects.filter(users=request.user)
    serializer = ChatSerializer(queryset, many=True)
    return render(request, 'messenger/home.html', {'chats': serializer.data})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            subject = 'Activate Your MSG Account'
            message = render_to_string('messenger/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)
            return redirect('account_activation_sent')
    else:
        form = SignUpForm()
    return render(request, 'messenger/signup.html', {'form': form})


def account_activation_sent(request):
    return render(request, 'messenger/account_activation_sent.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('home')
    else:
        return render(request, 'messenger/account_activation_invalid.html')


@login_required(login_url='/login/')
def chat(request, chat_id):
    queryset = Chat.objects.filter(users=request.user)
    serialized_chats_list = ChatSerializer(queryset, many=True).data

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return render(request, 'messenger/chat_not_found.html', {'chats': serialized_chats_list})

    if request.user not in chat.users.all():
        return render(request, 'messenger/chat_not_found.html', {'chats': serialized_chats_list})

    serialized_chat = ExtendedChatSerializer(chat, many=False).data

    return render(request, 'messenger/chat.html', {
        'chat_id': chat_id,
        'chat': serialized_chat,
        'chats': serialized_chats_list,
    })


@login_required(login_url='/login/')
def chat_info(request, chat_id):
    queryset = Chat.objects.filter(users=request.user)
    serialized_chats_list = ChatSerializer(queryset, many=True).data

    try:
        chat = Chat.objects.get(id=chat_id)
    except Chat.DoesNotExist:
        return render(request, 'messenger/chat_not_found.html', {'chats': serialized_chats_list})

    if request.user not in chat.users.all():
        return render(request, 'messenger/chat_not_found.html', {'chats': serialized_chats_list})

    serialized_chat = ExtendedChatSerializer(chat, many=False).data

    return render(request, 'messenger/chat_info.html', {
        'chat_id': chat_id,
        'chat': serialized_chat,
        'chats': serialized_chats_list,
    })


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def user_chats_list(self, request):
        user = request.user
        chats = Chat.objects.filter(users=user)
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave_chat(self, request, pk=None):
        user = request.user
        chat_id = pk
        chat = Chat.objects.get(id=chat_id)
        chat.users.remove(user)
        chat.save()
        return Response({'status': 'ok'})

    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        username = request.data.get('username')
        user = User.objects.get(username=username)
        chat_id = pk
        chat = Chat.objects.get(id=chat_id)
        if user not in chat.users.all():
            chat.users.add(user)
            chat.save()
        return Response({'status': 'ok'})


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False)
    def chat_messages_list(self, request):
        chat_id = request.query_params.get('chat_id')
        messages = Message.objects.filter(chat_id=chat_id).order_by('-number')
        page = self.paginate_queryset(messages)

        if page is not None:
            serializer = ExtendedMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ExtendedMessageSerializer(messages, many=True)
        return Response(serializer.data)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = (IsAuthenticated,)



class MessageListAPIView(ListAPIView):
    queryset = Message.objects.all()
    serializer_class = ExtendedMessageSerializer
    permission_classes = (IsAuthenticated,)

    def __init__(self):
        super().__init__()
        self.pagination_class.page_size = 30

    def get(self, request, *args, **kwargs):
        if 'chat_id' in request.GET:
            self.queryset = self.queryset.filter(chat_id=request.GET['chat_id']).order_by('-number')
        if 'begin' in request.GET:
            begin = int(request.GET['begin'])
            self.queryset = self.get_queryset()[begin:]
        if 'end' in request.GET:
            end = int(request.GET['end'])
            self.queryset = self.get_queryset()[:end]

        return self.list(request, *args, **kwargs)


