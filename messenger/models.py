from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User


User._meta.get_field('email')._unique = True
User._meta.get_field('email').blank = False
User._meta.get_field('email').null = False


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    photo = models.ImageField(upload_to='static/messenger/profile_photos', blank=True)
    email_confirmed = models.BooleanField(default=False)

    def email(self):
        return self.user.email

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        Profile.objects.create(user=instance)


class Chat(models.Model):
    name = models.CharField(max_length=255, blank=True)
    users = models.ManyToManyField(User, related_name='chats')
    photo = models.ImageField(upload_to='static/messenger/chat_photos', blank=True, null=True)

    def __str__(self):
        return str(self.id)


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
    number = models.PositiveIntegerField(default=0)
    timestamp = models.DateTimeField(auto_now_add=True)

    def Meta(self):
        unique_together = ("chat", "number")

    def __str__(self):
        return str(self.id)

    def save(self, *args, **kwargs):
        number = calc_msg_number(self.chat)
        self.number = number
        super(Message, self).save(*args, **kwargs)
