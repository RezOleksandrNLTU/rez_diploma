from urllib.request import urlopen
from os.path import basename

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File
from django.utils.translation import gettext_lazy as _


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

User.add_to_class("__str__", lambda self: f'{self.first_name} {self.last_name} {self.email}')
User._meta.verbose_name = 'Користувач'
User._meta.verbose_name_plural = 'Користувачі'


class Group(models.Model):
    class DegreeChoices(models.TextChoices):
        BACHELOR = 'bachelor', _('бакалавр')
        MASTER = 'master', _('магістр')

    name = models.CharField(max_length=255, unique=True, verbose_name='Назва групи')
    code = models.CharField(max_length=255, unique=True, verbose_name='Код групи')

    study_year = models.IntegerField(blank=True, null=True, verbose_name='Курс')
    speciality = models.CharField(max_length=255, blank=True, verbose_name='Спеціальність')
    institute = models.CharField(max_length=255, blank=True, verbose_name='Інститут')
    faculty = models.CharField(max_length=255, blank=True, verbose_name='Кафедра')
    degree = models.CharField(max_length=255, choices=DegreeChoices.choices, blank=True, verbose_name='Ступінь')

    def __str__(self):
        return str(f'Група {self.name}')

    class Meta:
        verbose_name = 'Група'
        verbose_name_plural = 'Групи'

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

    def get_degree(self):
        return self.DegreeChoices(self.degree).label


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Користувач')
    bio = models.TextField(max_length=500, blank=True, verbose_name='Про себе')
    photo = models.ImageField(upload_to='static/messenger/profile_photos', blank=True, verbose_name='Фото')
    email_confirmed = models.BooleanField(default=False, verbose_name='Підтвердження пошти')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Група')
    is_teacher = models.BooleanField(default=False, verbose_name='Є викладачем')

    patronymic = models.CharField(max_length=255, blank=True, verbose_name='По-батькові')
    diploma_supervisor_1 = models.CharField(max_length=255, blank=True, verbose_name='Керівник диплому 1')
    diploma_supervisor_2 = models.CharField(max_length=255, blank=True, verbose_name='Керівник диплому 2')
    diploma_topic = models.CharField(max_length=255, blank=True, verbose_name='Тема диплому')
    diploma_reviewer = models.CharField(max_length=255, blank=True, verbose_name='Рецензент')
    diploma_reviewer_position = models.CharField(max_length=255, blank=True, verbose_name='Посада рецензента')

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name} {self.user.email}'

    class Meta:
        verbose_name = 'Профіль'
        verbose_name_plural = 'Профілі'

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


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    try:
        instance.profile.save()
    except ObjectDoesNotExist:
        Profile.objects.create(user=instance)


class Chat(models.Model):

    class ChatTypes(models.TextChoices):
        PRIVATE = 'private', _('приватний')
        GROUP = 'group', _('груповий')
        DIPLOMA = 'diploma', _('дипломний')

    name = models.CharField(max_length=255, verbose_name='Назва чату')
    users = models.ManyToManyField(User, related_name='chats', verbose_name='Користувачі')
    photo = models.ImageField(upload_to='static/messenger/chat_photos', blank=True, null=True, verbose_name='Фото')
    type = models.CharField(max_length=255, choices=ChatTypes.choices, default=ChatTypes.GROUP, verbose_name='Тип чату')
    creator = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Творець чату')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, blank=True, null=True, verbose_name='Група')

    def __str__(self):
        return str(f'Чат {self.name} {self.ChatTypes(self.type).label}')

    class Meta:
        verbose_name = 'Чат'
        verbose_name_plural = 'Чати'

    def is_user_in_chat(self, user):
        return self.users.filter(id=user.id).exists()


def calc_msg_number(chat):
    present_numbers = Message.objects.filter(chat=chat).order_by('-number').values_list('number', flat=True)
    if present_numbers:
        return present_numbers[0] + 1
    else:
        return 0


class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, verbose_name='Чат')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Користувач')
    text = models.TextField(verbose_name='Текст повідомлення')
    file = models.FileField(upload_to='static/messenger/message_files', blank=True, null=True, verbose_name='Файл')
    number = models.PositiveIntegerField(default=0, verbose_name='Номер повідомлення')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Дата надсилання')
    pinned = models.BooleanField(default=False, verbose_name='Закріплено')

    class Meta:
        verbose_name = 'Повідомлення'
        verbose_name_plural = 'Повідомлення'

        unique_together = ("chat", "number")

    def __str__(self):
        return f'{self.chat} {self.user} {self.number}'

    def save(self, *args, **kwargs):
        if not self.pk:
            number = calc_msg_number(self.chat)
            self.number = number
        super(Message, self).save(*args, **kwargs)
