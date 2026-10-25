import logging
from datetime import timedelta
from secrets import randbelow
from smtplib import SMTPException

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render, redirect
from django.utils import timezone
from requests import RequestException

from .forms import EmailVerificationForm, PhoneVerificationForm, RegisterForm
from .models import EmailVerification, PhoneVerification
from .verification import (
    PhoneDeliveryError,
    check_phone_verification_code,
    send_phone_verification_code,
    send_verification_email,
)

logger = logging.getLogger(__name__)
User = get_user_model()
PENDING_VERIFICATION_SESSION_KEY = 'pending_verification_user_id'
EMAIL_CODE_LIFETIME = timedelta(minutes=10)
EMAIL_CODE_RESEND_DELAY = timedelta(seconds=60)
PHONE_CODE_LIFETIME = timedelta(minutes=10)
PHONE_CODE_RESEND_DELAY = timedelta(seconds=60)
PHONE_CODE_MAX_ATTEMPTS = 5
EMAIL_CODE_MAX_ATTEMPTS = 5


class EmailCodeResendTooSoon(Exception):
    pass


def _pending_user(request):
    user_id = request.session.get(PENDING_VERIFICATION_SESSION_KEY)
    if not user_id:
        return None
    return User.objects.filter(pk=user_id, is_active=False).first()


def _activate_if_verified(request, user):
    if not user.email_verified:
        return False

    user.is_verified = True
    user.is_active = True
    user.save(update_fields=('is_verified', 'is_active'))
    request.session.pop(PENDING_VERIFICATION_SESSION_KEY, None)
    login(request, user, backend=settings.AUTHENTICATION_BACKENDS[0])
    return True


def _send_phone_code(user):
    now = timezone.now()
    verification, _ = PhoneVerification.objects.get_or_create(
        user=user,
        defaults={
            'code_hash': '',
            'expires_at': now,
            'last_sent_at': now - PHONE_CODE_RESEND_DELAY,
        }
    )
    if now - verification.last_sent_at < PHONE_CODE_RESEND_DELAY:
        raise PhoneDeliveryError('Please wait before requesting another code.')

    verification.provider_reference = send_phone_verification_code(user.phone_number)
    verification.code_hash = ''
    verification.expires_at = now + PHONE_CODE_LIFETIME
    verification.last_sent_at = now
    verification.failed_attempts = 0
    verification.save()
    return verification


def _new_email_code(user):
    now = timezone.now()
    verification, _ = EmailVerification.objects.get_or_create(
        user=user,
        defaults={
            'code_hash': '',
            'expires_at': now,
            'last_sent_at': now - EMAIL_CODE_RESEND_DELAY,
        }
    )
    if now - verification.last_sent_at < EMAIL_CODE_RESEND_DELAY:
        raise EmailCodeResendTooSoon('Please wait before requesting another code.')

    code = f'{randbelow(1_000_000):06d}'
    verification.code_hash = make_password(code)
    verification.expires_at = now + EMAIL_CODE_LIFETIME
    verification.last_sent_at = now
    verification.failed_attempts = 0
    verification.save()
    return verification, code


def _deliver_verification_messages(user):
    failures = []
    try:
        _, code = _new_email_code(user)
        send_verification_email(user, code)
    except (ImproperlyConfigured, OSError, RuntimeError, SMTPException):
        logger.exception('Email verification delivery failed.')
        failures.append('email')
    return failures


def _email_uses_console_backend():
    return settings.EMAIL_BACKEND == 'django.core.mail.backends.console.EmailBackend'


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        request.session[PENDING_VERIFICATION_SESSION_KEY] = user.pk

        failures = _deliver_verification_messages(user)
        if failures:
            messages.error(
                request,
                'Your account is pending verification, but we could not send your '
                f'{" and ".join(failures)} verification message. Please retry below.'
            )
        elif _email_uses_console_backend():
            messages.warning(
                request,
                'Development email mode is enabled: the verification code was written '
                'to the server terminal, not sent to your inbox. Configure an SMTP '
                'email backend to deliver it.'
            )
        else:
            messages.info(
                request,
                'We sent a six-digit verification code to your email. Phone '
                'verification is not required.'
            )
        return redirect('verification_pending')

    return render(request, 'users/register.html', {'form': form})


def verification_pending_view(request):
    user = _pending_user(request)
    if user is None:
        messages.info(request, 'Create an account to begin contact verification.')
        return redirect('register')
    return render(
        request,
        'users/verification_pending.html',
        {
            'account': user,
            'email_form': EmailVerificationForm(),
            'phone_form': PhoneVerificationForm(),
            'email_console_backend': _email_uses_console_backend(),
        }
    )


def verify_email_view(request):
    user = _pending_user(request)
    if user is None:
        messages.info(request, 'Create an account to begin contact verification.')
        return redirect('register')

    form = EmailVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        verification = EmailVerification.objects.filter(user=user).first()
        if verification is None or not verification.code_hash:
            form.add_error(None, 'No active email code was found. Request a new code.')
        elif verification.expires_at <= timezone.now():
            form.add_error(None, 'That code has expired. Request a new code.')
        elif verification.failed_attempts >= EMAIL_CODE_MAX_ATTEMPTS:
            form.add_error(None, 'Too many incorrect attempts. Request a new code.')
        elif not check_password(form.cleaned_data['code'], verification.code_hash):
            verification.failed_attempts += 1
            verification.save(update_fields=('failed_attempts',))
            form.add_error('code', 'That code is incorrect.')
        else:
            user.email_verified = True
            user.save(update_fields=('email_verified',))
            verification.delete()
            if _activate_if_verified(request, user):
                messages.success(
                    request,
                    'Your email is verified. Your account is active.'
                )
                return redirect('home')
            messages.success(
                request,
                'Your email is verified. Your account is active.'
            )
            return redirect('verification_pending')

    return render(
        request,
        'users/verification_pending.html',
        {
            'account': user,
            'email_form': form,
            'phone_form': PhoneVerificationForm(),
            'email_console_backend': _email_uses_console_backend(),
        }
    )


def verify_phone_view(request):
    user = _pending_user(request)
    if user is None:
        messages.info(request, 'Create an account to begin contact verification.')
        return redirect('register')

    form = PhoneVerificationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        verification = PhoneVerification.objects.filter(user=user).first()
        if verification is None:
            form.add_error(None, 'No active phone code was found. Request a new code.')
        elif verification.expires_at <= timezone.now():
            form.add_error(None, 'That code has expired. Request a new code.')
        elif verification.failed_attempts >= PHONE_CODE_MAX_ATTEMPTS:
            form.add_error(None, 'Too many incorrect attempts. Request a new code.')
        else:
            try:
                if not verification.provider_reference:
                    raise PhoneDeliveryError(
                        'No active phone code was found. Request a new code.'
                    )
                code_is_valid = check_phone_verification_code(
                    verification.provider_reference,
                    form.cleaned_data['code'],
                )
            except PhoneDeliveryError as error:
                form.add_error(None, str(error))
            except (ImproperlyConfigured, RequestException):
                logger.exception('Phone verification check failed.')
                form.add_error(
                    None,
                    'We could not check your phone code right now. Please try again later.'
                )
            else:
                if not code_is_valid:
                    verification.failed_attempts += 1
                    verification.save(update_fields=('failed_attempts',))
                    form.add_error('code', 'That code is incorrect.')
                else:
                    user.phone_verified = True
                    user.save(update_fields=('phone_verified',))
                    verification.delete()
                    if _activate_if_verified(request, user):
                        messages.success(
                            request,
                            'Your email and phone are verified. Your account is active.'
                        )
                        return redirect('home')
                    messages.success(
                        request,
                        'Your phone is verified. Verify your email to activate your account.'
                    )
                    return redirect('verification_pending')

    return render(
        request,
        'users/verification_pending.html',
        {
            'account': user,
            'email_form': EmailVerificationForm(),
            'phone_form': form,
            'email_console_backend': _email_uses_console_backend(),
        }
    )


def resend_verification_email_view(request):
    if request.method != 'POST':
        return redirect('verification_pending')
    user = _pending_user(request)
    if user is None:
        messages.info(request, 'Create an account to begin contact verification.')
        return redirect('register')
    if user.email_verified:
        messages.info(request, 'Your email address is already verified.')
        return redirect('verification_pending')

    try:
        _, code = _new_email_code(user)
        send_verification_email(user, code)
        if _email_uses_console_backend():
            messages.warning(
                request,
                'Development email mode is enabled: the verification code was written '
                'to the server terminal, not sent to your inbox.'
            )
        else:
            messages.success(request, 'A new verification code has been sent to your email.')
    except EmailCodeResendTooSoon as error:
        messages.warning(request, str(error))
    except (ImproperlyConfigured, OSError, RuntimeError, SMTPException):
        logger.exception('Email verification resend failed.')
        messages.error(request, 'We could not send the verification email. Please try again later.')
    return redirect('verification_pending')


def resend_phone_code_view(request):
    if request.method != 'POST':
        return redirect('verification_pending')
    user = _pending_user(request)
    if user is None:
        messages.info(request, 'Create an account to begin contact verification.')
        return redirect('register')
    if user.phone_verified:
        messages.info(request, 'Your phone number is already verified.')
        return redirect('verification_pending')

    try:
        _send_phone_code(user)
        messages.success(request, 'A new verification code has been sent to your phone.')
    except PhoneDeliveryError as error:
        messages.warning(request, str(error))
    except (ImproperlyConfigured, RequestException, RuntimeError):
        logger.exception('Phone verification resend failed.')
        messages.error(request, 'We could not send the verification code. Please try again later.')
    return redirect('verification_pending')


def login_view(request):

    form = AuthenticationForm(
        request,
        data=request.POST if request.method == 'POST' else None
    )
    form.fields['username'].widget.attrs['placeholder'] = 'Enter your username'
    form.fields['password'].widget.attrs['placeholder'] = 'Enter your password'

    if request.method == 'POST':

        username = request.POST.get('username')

        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:

            login(request, user)

            return redirect('dashboard')

    return render(
        request,
        'users/login.html',
        {'form': form}
    )


def logout_view(request):

    logout(request)

    return redirect('home')
