from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


# Create your forms here.

class SignUpForm(UserCreationForm):
	first_name = forms.CharField(max_length=30, required=True, help_text='Required.')
	last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
	email = forms.EmailField(max_length=254, required=True, help_text='Required.')

	class Meta:
		model = User
		fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

	def save(self, commit=True):
		user = super(SignUpForm, self).save(commit=False)
		user.email = self.cleaned_data['email']
		if commit:
			user.save()
		return user


class CustomUserCreationForm(UserCreationForm):
	class Meta(UserCreationForm):
		model = User
		fields = UserCreationForm.Meta.fields + ('email', )

