import re

from django import forms


class MpesaCheckoutForm(forms.Form):
    phone_number = forms.CharField(
        label='M-Pesa phone number',
        max_length=16,
        widget=forms.TextInput(attrs={
            'autocomplete': 'tel',
            'inputmode': 'tel',
            'placeholder': '+254 712 345 678',
        }),
    )

    def clean_phone_number(self):
        phone_number = re.sub(r'[\s()-]', '', self.cleaned_data['phone_number'])
        if not re.fullmatch(r'(?:\+?254|0)(?:7|1)\d{8}', phone_number):
            raise forms.ValidationError(
                'Enter a valid Kenyan M-Pesa number, such as +254712345678.'
            )
        return phone_number
