import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail


class VerificationDeliveryError(RuntimeError):
    pass


class PhoneDeliveryError(VerificationDeliveryError):
    pass


def send_verification_email(user, code):
    sent_count = send_mail(
        subject='Your AssetLinkAfrica email verification code',
        message=(
            f'Hello {user.username},\n\n'
            'Use this one-time code to verify your email address:\n\n'
            f'{code}\n\n'
            'The code expires in 10 minutes and can be used only once.\n\n'
            'If you did not create this account, you can ignore this email.'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    if sent_count != 1:
        raise VerificationDeliveryError('Email backend did not deliver the verification code.')


def send_phone_verification_code(phone_number):
    api_key = settings.TERMII_API_KEY
    sender_id = settings.TERMII_SENDER_ID
    if not api_key or not sender_id:
        raise ImproperlyConfigured(
            'Configure TERMII_API_KEY and TERMII_SENDER_ID to send phone verification SMS.'
        )

    response = requests.post(
        f'{settings.TERMII_API_BASE_URL.rstrip("/")}/api/sms/otp/send',
        json={
            'api_key': api_key,
            'message_type': 'NUMERIC',
            'to': phone_number.lstrip('+'),
            'from': sender_id,
            'channel': 'generic',
            'pin_attempts': 5,
            'pin_time_to_live': 10,
            'pin_length': 6,
            'pin_placeholder': '< 123456 >',
            'message_text': (
                'Your AssetLinkAfrica verification code is < 123456 >. '
                'It expires in 10 minutes.'
            ),
            'pin_type': 'NUMERIC',
        },
        timeout=10,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as error:
        raise PhoneDeliveryError('Termii returned an invalid OTP response.') from error
    if not isinstance(payload, dict):
        raise PhoneDeliveryError('Termii returned an invalid OTP response.')

    pin_id = payload.get('pinId')
    if not isinstance(pin_id, str) or not pin_id:
        raise PhoneDeliveryError('Termii did not accept the phone verification request.')
    return pin_id


def check_phone_verification_code(pin_id, code):
    api_key = settings.TERMII_API_KEY
    if not api_key:
        raise ImproperlyConfigured(
            'Configure TERMII_API_KEY to check phone verification codes.'
        )

    response = requests.post(
        f'{settings.TERMII_API_BASE_URL.rstrip("/")}/api/sms/otp/verify',
        json={
            'api_key': api_key,
            'pin_id': pin_id,
            'pin': code,
        },
        timeout=10,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as error:
        raise PhoneDeliveryError('Termii returned an invalid OTP verification response.') from error
    if not isinstance(payload, dict):
        raise PhoneDeliveryError('Termii returned an invalid OTP verification response.')

    verified = payload.get('verified')
    if verified is True or (
        isinstance(verified, str) and verified.lower() == 'true'
    ):
        return True
    if verified is False or (
        isinstance(verified, str) and verified.lower() == 'false'
    ):
        return False
    raise PhoneDeliveryError('Termii returned an unexpected OTP verification response.')
