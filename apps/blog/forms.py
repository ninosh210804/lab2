from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms

from .models import User


class BlogUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")


class BlogUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"
