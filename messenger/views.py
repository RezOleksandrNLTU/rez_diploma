from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.models import User

from .forms import SignUpForm
from .tokens import account_activation_token
from .models import Chat
from .serializers import ChatSerializer, ExtendedChatSerializer


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
