from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class RegisterForm(UserCreationForm):

    class Meta:

        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2'
        ]

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'placeholder': 'Username',
                    'autocomplete': 'username',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'placeholder': 'Email',
                    'autocomplete': 'email',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update(
            {
                'placeholder': 'Password',
                'autocomplete': 'new-password',
            }
        )
        self.fields['password2'].label = 'Confirm password'
        self.fields['password2'].widget.attrs.update(
            {
                'placeholder': 'Confirm Password',
                'autocomplete': 'new-password',
            }
        )
