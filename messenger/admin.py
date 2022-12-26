from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import Profile, Chat, Message
from .forms import CustomUserCreationForm


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email')
    search_fields = ('user__username',)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'profile'


class UserAdminCustom(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('id', ) + UserAdmin.list_display + ('is_active',)
    list_filter = UserAdmin.list_filter + ('profile__email_confirmed',)
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('email',)}),
    )

    inlines = (ProfileInline,)


class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


class MessageAdmin(admin.ModelAdmin):
    list_display = ('number', 'chat', 'user', 'text', 'timestamp')

    list_filter = ('chat', )


admin.site.register(Profile, ProfileAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
