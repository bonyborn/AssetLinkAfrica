from django import forms

from .models import Payment
from .mpesa import normalize_phone_number


class SubscriptionCheckoutForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHODS,
        widget=forms.RadioSelect,
    )
    phone_number = forms.CharField(
        label='M-Pesa phone number',
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={
            'autocomplete': 'tel',
            'inputmode': 'tel',
            'placeholder': '+254 712 345 678',
        }),
    )
    bank_transfer_reference = forms.CharField(
        label='Bank transfer reference',
        max_length=100,
        required=False,
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')

        if payment_method == 'mpesa' and cleaned_data.get('phone_number'):
            try:
                cleaned_data['phone_number'] = normalize_phone_number(
                    cleaned_data['phone_number']
                )
            except ValueError as error:
                self.add_error('phone_number', str(error))
        elif payment_method == 'mpesa':
            self.add_error('phone_number', 'Enter your M-Pesa phone number.')

        if payment_method == 'bank' and not cleaned_data.get('bank_transfer_reference', '').strip():
            self.add_error(
                'bank_transfer_reference',
                'Enter the reference shown on your bank transfer.',
            )
        elif payment_method == 'bank':
            cleaned_data['bank_transfer_reference'] = (
                cleaned_data['bank_transfer_reference'].strip()
            )

        return cleaned_data
