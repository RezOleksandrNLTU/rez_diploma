from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User, Group as UserGroup
from django.contrib.sites.models import Site


from .models import Profile, Chat, Message, Group, DocumentTemplate
from .forms import CustomUserCreationForm


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'email')
    search_fields = ('user__username',)
    exclude = ('bio', 'email_confirmed',)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Профілі'

    exclude = ('bio', 'email_confirmed',)


class UserAdminCustom(UserAdmin):
    add_form = CustomUserCreationForm
    list_display = ('id', ) + UserAdmin.list_display + ('is_active',)
    # list_filter = UserAdmin.list_filter + ('profile__email_confirmed',)
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


class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

    def get_form(self, request, obj=None, **kwargs):
        help_text = """
    Для вставки даних в шаблон використовуйте наступні теги (тег: пояснення)<br><br>
institute: інститут<br>
faculty: кафедра\n<br>
degree: ступінь<br>
diploma_topic: тема диплому<br>
study_year: курс<br>
group: група<br>
speciality: спеціальність<br>
first_name: ім'я<br>
last_name: прізвище<br>
patronymic: по-батькові<br>
diploma_supervisor_1: керівник диплому<br>
diploma_supervisor_2: керівник диплому<br>
diploma_reviewer: рецензент<br>
diploma_reviewer_position: посада рецензента<br><br>

Теги вставляються в шаблон таким чином: {{тег}}
        """

        form = super(DocumentTemplateAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['template_file'].help_text = help_text
        return form


admin.site.register(Profile, ProfileAdmin)
admin.site.unregister(User)
admin.site.register(User, UserAdminCustom)
admin.site.register(Chat, ChatAdmin)
admin.site.register(Message, MessageAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(DocumentTemplate, DocumentTemplateAdmin)

admin.site.unregister(Site)
admin.site.unregister(UserGroup)

admin.site.site_header = 'Месенджер НЛТУ'
