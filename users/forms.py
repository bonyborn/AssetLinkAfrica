from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(
        label='Phone number (include country code)',
        max_length=16,
        help_text='Use international format, for example +254712345678.'
    )
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={
            'required': 'You must agree to the Terms and Conditions and Privacy Policy.'
        }
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data['phone_number'].strip()
        if not phone_number.startswith('+') or not phone_number[1:].isdigit():
            raise ValidationError(
                'Enter a valid phone number in international format, such as +254712345678.'
            )
        if not 8 <= len(phone_number[1:]) <= 15:
            raise ValidationError('Enter a valid international phone number.')
        return phone_number

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'password1',
            'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'Choose a username',
            'email': 'you@example.com',
            'phone_number': '+254712345678',
            'password1': 'Create a password',
            'password2': 'Confirm your password',
        }
        for field_name, placeholder in placeholders.items():
            self.fields[field_name].widget.attrs['placeholder'] = placeholder


class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        label='Verification code',
        min_length=6,
        max_length=6,
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'pattern': '[0-9]{6}',
        })
    )

    def clean_code(self):
        code = self.cleaned_data['code'].strip()
        if not code.isdigit():
            raise ValidationError('Enter the six-digit verification code.')
        return code


class EmailVerificationForm(VerificationCodeForm):
    pass


class PhoneVerificationForm(VerificationCodeForm):
    pass
