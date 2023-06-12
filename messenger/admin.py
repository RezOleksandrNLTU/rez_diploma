from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group as UserGroup
from django.contrib.sites.models import Site
from rest_framework.authtoken.models import TokenProxy
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken


from .models import Profile, Chat, Message, Group
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


class GroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


admin.site.register(Profile, ProfileAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Group, GroupAdmin)

admin.site.unregister(Site)
admin.site.unregister(UserGroup)
admin.site.unregister(TokenProxy)
admin.site.unregister(EmailAddress)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialToken)

admin.site.site_header = 'Месенджер НЛТУ'
