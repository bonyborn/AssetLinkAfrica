import base64
import re
from decimal import Decimal
from secrets import token_hex

import requests
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

class MpesaError(RuntimeError):
    pass


def normalize_phone_number(phone_number):
    phone_number = phone_number.strip()
    if not re.fullmatch(r'(?:\+?254|0)(?:7|1)\d{8}', phone_number):
        raise ValueError('Enter a valid Kenyan M-Pesa number.')

    digits = phone_number.lstrip('+')
    return f'254{digits[1:]}' if digits.startswith('0') else digits


def _configuration():
    required_settings = (
        'MPESA_CONSUMER_KEY',
        'MPESA_CONSUMER_SECRET',
        'MPESA_SHORTCODE',
        'MPESA_PASSKEY',
        'MPESA_CALLBACK_URL',
    )
    missing = [
        name for name in required_settings
        if not getattr(settings, name, '')
    ]
    callback_url = getattr(settings, 'MPESA_CALLBACK_URL', '')
    if callback_url and not callback_url.startswith('https://'):
        missing.append('MPESA_CALLBACK_URL (must use HTTPS)')

    if missing:
        raise ImproperlyConfigured(
            f'Configure the M-Pesa Daraja settings: {", ".join(missing)}.'
        )

    return settings.MPESA_API_BASE_URL.rstrip('/')


def _response_payload(response, operation):
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as error:
        raise MpesaError(f'M-Pesa returned an invalid {operation} response.') from error
    if not isinstance(payload, dict):
        raise MpesaError(f'M-Pesa returned an invalid {operation} response.')
    return payload


def initiate_stk_push(
    payment,
    phone_number,
    transaction_description='Asset booking',
):
    base_url = _configuration()
    auth_response = requests.get(
        f'{base_url}/oauth/v1/generate',
        params={'grant_type': 'client_credentials'},
        auth=(
            settings.MPESA_CONSUMER_KEY,
            settings.MPESA_CONSUMER_SECRET,
        ),
        timeout=15,
    )
    auth_payload = _response_payload(auth_response, 'authentication')
    access_token = auth_payload.get('access_token')
    if not isinstance(access_token, str) or not access_token:
        raise MpesaError('M-Pesa did not return an access token.')

    timestamp = timezone.localtime().strftime('%Y%m%d%H%M%S')
    password = base64.b64encode(
        f'{settings.MPESA_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}'.encode()
    ).decode()
    payment_amount = Decimal(str(payment.amount))
    amount = int(payment_amount.to_integral_value())
    if amount < 1:
        raise MpesaError('The booking amount must be at least KES 1.')
    if payment_amount != Decimal(amount):
        raise MpesaError('M-Pesa payments must be whole Kenyan shillings.')

    response = requests.post(
        f'{base_url}/mpesa/stkpush/v1/processrequest',
        headers={'Authorization': f'Bearer {access_token}'},
        json={
            'BusinessShortCode': settings.MPESA_SHORTCODE,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': settings.MPESA_TRANSACTION_TYPE,
            'Amount': amount,
            'PartyA': phone_number,
            'PartyB': settings.MPESA_SHORTCODE,
            'PhoneNumber': phone_number,
            'CallBackURL': settings.MPESA_CALLBACK_URL,
            'AccountReference': f'ALA{token_hex(4).upper()}',
            'TransactionDesc': transaction_description[:13],
        },
        timeout=15,
    )
    payload = _response_payload(response, 'STK push')
    if payload.get('ResponseCode') != '0':
        message = payload.get('ResponseDescription') or 'M-Pesa rejected the payment request.'
        raise MpesaError(str(message))

    checkout_request_id = payload.get('CheckoutRequestID')
    if not isinstance(checkout_request_id, str) or not checkout_request_id:
        raise MpesaError('M-Pesa did not return a checkout request ID.')

    payment.phone_number = phone_number
    payment.checkout_request_id = checkout_request_id
    payment.result_description = str(
        payload.get('CustomerMessage') or 'Payment request sent to your phone.'
    )[:255]
    payment.save(update_fields=(
        'phone_number',
        'checkout_request_id',
        'result_description',
    ))
    return payment


def callback_metadata(callback):
    body = callback.get('Body')
    stk_callback = body.get('stkCallback') if isinstance(body, dict) else None
    if not isinstance(stk_callback, dict):
        raise ValueError('M-Pesa callback did not include an STK callback.')

    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    if not isinstance(checkout_request_id, str) or not checkout_request_id:
        raise ValueError('M-Pesa callback is missing its checkout request ID.')
    if not isinstance(result_code, (int, str)) or not str(result_code).isdigit():
        raise ValueError('M-Pesa callback has an invalid result code.')

    metadata = {}
    callback_metadata = stk_callback.get('CallbackMetadata', {})
    items = callback_metadata.get('Item', []) if isinstance(callback_metadata, dict) else []
    if not isinstance(items, list):
        raise ValueError('M-Pesa callback metadata is invalid.')
    for item in items:
        if isinstance(item, dict) and isinstance(item.get('Name'), str):
            metadata[item['Name']] = item.get('Value')

    return checkout_request_id, int(result_code), stk_callback, metadata


def callback_amount_matches(value, expected):
    try:
        amount = Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return False
    return amount.is_finite() and amount == expected
