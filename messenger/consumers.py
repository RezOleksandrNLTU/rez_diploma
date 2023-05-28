# chat/consumers.py
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from .models import Chat, Message
from .serializers import MessageSerializer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return

        self.chat_id = self.scope['url_route']['kwargs']['chat_id']

        try:
            self.chat = Chat.objects.get(id=self.chat_id)
        except Chat.DoesNotExist:
            self.close()
            return

        self.chat_group_name = 'chat_%s' % self.chat_id


        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.chat_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        user = self.scope['user']
        if not user.is_authenticated:
            return
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.chat_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return

        text_data_json = json.loads(text_data)
        text = text_data_json['text']

        message = Message(chat=self.chat, user=user, text=text)
        message.save()

        # serialise message
        serialized_message = MessageSerializer(message).data
        serialized_message['type'] = 'chat_message'

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.chat_group_name,
            serialized_message
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event

        # Send message to WebSocket
        self.send(text_data=json.dumps(message))
