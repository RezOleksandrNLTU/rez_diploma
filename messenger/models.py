from urllib.request import urlopen
from os.path import basename

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File


User._meta.get_field('email')._unique = True
User._meta.get_field('email').blank = False
User._meta.get_field('email').null = False

User._meta.get_field('username')._unique = False
User._meta.USERNAME_FIELD = 'email'
User.USERNAME_FIELD = 'email'
User.REQUIRED_FIELDS.remove('email')
User._meta.get_field('username').blank = False
User._meta.get_field('username').null = False

User._meta.get_field('password').blank = False
User._meta.get_field('password').null = False

User.add_to_class("__str__", lambda self: self.email)


class Group(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    code = models.CharField(max_length=255, blank=True, unique=True)

    def __str__(self):
        return str(f'Група {self.name}(id={self.id})')

    class Meta:
        verbose_name = 'Student group'
        verbose_name_plural = 'Student groups'

    def save(
        self, force_insert=False, force_update=False, using=None, update_fields=None
    ):
        if not self.code:
            self.code = self.name

        group_chat = Chat.objects.filter(name=self.name, type='group', group=self)
        if not group_chat:
            group_chat = Chat.objects.create(name=f'Дипломний чат {self.name}', type=Chat.CHAT_TYPES[2][0],
                                             group=self)
            group_users = Profile.objects.filter(group=self)
            for user in group_users:
                group_chat.users.add(user.user)
            group_chat.save()
        super().save(force_insert, force_update, using, update_fields)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    photo = models.ImageField(upload_to='static/messenger/profile_photos', blank=True)
    email_confirmed = models.BooleanField(default=False)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)
    is_teacher = models.BooleanField(default=False)

    def email(self):
        return self.user.email

    def get_photo_from_url(self, url):
        photo_tmp = NamedTemporaryFile()
        with urlopen(url) as uo:
            assert uo.status == 200
            photo_tmp.write(uo.read())
            photo_tmp.flush()
        photo = File(photo_tmp)
        file_name = basename(photo_tmp.name) + '.jpg'
        self.photo.save(basename(file_name), photo)
        photo_tmp.close()

    def __str__(self):
        return self.user.email


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        Profile.objects.create(user=instance)


class Chat(models.Model):
    CHAT_TYPES = (
        ('private', 'private'),
        ('group', 'group'),
        ('diploma', 'diploma'),
    )

    name = models.CharField(max_length=255)
    users = models.ManyToManyField(User, related_name='chats')
    photo = models.ImageField(upload_to='static/messenger/chat_photos', blank=True, null=True)
    type = models.CharField(max_length=255, choices=CHAT_TYPES, default='group')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        if self.creator:
            return str(f'Чат {self.name}(id={self.id}, type={self.type}, creator={self.creator.username})')
        return str(f'Чат {self.name}(id={self.id}, type={self.type})')

    def is_user_in_chat(self, user):
        return self.users.filter(id=user.id).exists()


def calc_msg_number(chat):
    present_numbers = Message.objects.filter(chat=chat).order_by('-number').values_list('number', flat=True)
    if present_numbers:
        return present_numbers[0] + 1
    else:
        return 0


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='static/messenger/message_files', blank=True, null=True)
    number = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)
    pinned = models.BooleanField(default=False)

    def Meta(self):
        unique_together = ("chat", "number")

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        number = calc_msg_number(self.chat)
        self.number = number
        super(Message, self).save(*args, **kwargs)
