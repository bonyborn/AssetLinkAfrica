from django import forms

from .models import ContactMessage


class ContactForm(forms.Form):
    fullName = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your full name'}),
        error_messages={'required': 'Please enter your full name.'}
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email'}),
        error_messages={'required': 'Please enter your email address.', 'invalid': 'Please enter a valid email address.'}
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your phone number'})
    )
    subject = forms.ChoiceField(
        required=True,
        choices=(('', 'Select a subject'),) + ContactMessage.SUBJECT_CHOICES,
        error_messages={'required': 'Please select a subject.'}
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={'rows': 6, 'placeholder': 'Please provide details about your inquiry...'}
        ),
        error_messages={'required': 'Please write your message.'}
    )
    priority = forms.ChoiceField(
        required=False,
        choices=ContactMessage.PRIORITY_CHOICES,
        initial='medium'
    )
