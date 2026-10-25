from datetime import timedelta
import re
from unittest.mock import patch

from django.contrib.auth.hashers import make_password
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import RegisterForm
from .models import EmailVerification, PhoneVerification, User
from .views import PENDING_VERIFICATION_SESSION_KEY


class RegisterFormTests(TestCase):

    def test_terms_and_privacy_consent_is_required(self):
        form = RegisterForm(data={
            'username': 'consent-user',
            'email': 'consent@example.com',
            'phone_number': '+254712345678',
            'password1': 'Complex-test-password-948!',
            'password2': 'Complex-test-password-948!',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('terms_accepted', form.errors)

    def test_terms_and_privacy_consent_can_be_submitted(self):
        form = RegisterForm(data={
            'username': 'consent-user',
            'email': 'consent@example.com',
            'phone_number': '+254712345678',
            'password1': 'Complex-test-password-948!',
            'password2': 'Complex-test-password-948!',
            'terms_accepted': 'on',
        })

        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_fields_have_visible_placeholders(self):
        form = RegisterForm()

        self.assertEqual(
            form.fields['username'].widget.attrs['placeholder'],
            'Choose a username',
        )
        self.assertEqual(
            form.fields['phone_number'].widget.attrs['placeholder'],
            '+254712345678',
        )

    def test_email_and_international_phone_are_required(self):
        form = RegisterForm(data={
            'username': 'contact-user',
            'email': 'invalid-email',
            'phone_number': '0712345678',
            'password1': 'Complex-test-password-948!',
            'password2': 'Complex-test-password-948!',
            'terms_accepted': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('phone_number', form.errors)


class ContactVerificationFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='pending-user',
            email='pending@example.com',
            phone_number='+254712345678',
            password='Complex-test-password-948!',
            is_active=False,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_email_verification_message_contains_one_time_code(self):
        from .verification import send_verification_email

        send_verification_email(self.user, '123456')

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('123456', mail.outbox[0].body)
        self.assertIn('expires in 10 minutes', mail.outbox[0].body)
        self.assertIn(self.user.email, mail.outbox[0].recipients())

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend')
    @patch('users.views.send_phone_verification_code')
    @patch('users.views.send_verification_email')
    def test_registration_requires_email_verification_but_not_phone_verification(
        self,
        send_email,
        send_sms,
    ):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'new-user',
                'email': 'new@example.com',
                'phone_number': '+254712345678',
                'password1': 'Complex-test-password-948!',
                'password2': 'Complex-test-password-948!',
                'terms_accepted': 'on',
            }
        )

        self.assertRedirects(response, reverse('verification_pending'))
        user = User.objects.get(username='new-user')
        self.assertFalse(user.is_active)
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        self.assertTrue(EmailVerification.objects.filter(user=user).exists())
        self.assertFalse(PhoneVerification.objects.filter(user=user).exists())
        send_email.assert_called_once()
        send_sms.assert_not_called()
        pending_response = self.client.get(reverse('verification_pending'))
        self.assertContains(pending_response, 'Email is in development mode')
        self.assertContains(pending_response, 'verification code appears in the')
        self.assertContains(pending_response, 'Phone verification is not required.')
        self.assertContains(pending_response, 'Verify phone (optional)')

    def test_email_code_activates_account_without_phone_verification(self):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        EmailVerification.objects.create(
            user=self.user,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_email'),
            {'code': '123456'}
        )

        self.assertRedirects(response, reverse('home'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertFalse(self.user.phone_verified)
        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)
        self.assertFalse(EmailVerification.objects.filter(user=self.user).exists())

    def test_email_code_activates_account_only_after_phone_is_verified(self):
        self.user.phone_verified = True
        self.user.save(update_fields=('phone_verified',))
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        EmailVerification.objects.create(
            user=self.user,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_email'),
            {'code': '123456'}
        )

        self.assertRedirects(response, reverse('home'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertTrue(self.user.phone_verified)
        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)

    def test_expired_email_code_does_not_verify_account(self):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        EmailVerification.objects.create(
            user=self.user,
            code_hash=make_password('123456'),
            expires_at=timezone.now() - timedelta(seconds=1),
            last_sent_at=timezone.now() - timedelta(minutes=11),
        )

        response = self.client.post(
            reverse('verify_email'),
            {'code': '123456'}
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.assertFalse(self.user.is_active)
        self.assertContains(response, 'That code has expired.')

    def test_incorrect_email_code_is_counted(self):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        verification = EmailVerification.objects.create(
            user=self.user,
            code_hash=make_password('123456'),
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_email'),
            {'code': '999999'}
        )

        self.assertEqual(response.status_code, 200)
        verification.refresh_from_db()
        self.assertEqual(verification.failed_attempts, 1)
        self.assertContains(response, 'That code is incorrect.')

    @patch('users.views.check_phone_verification_code', return_value=True)
    def test_phone_code_activates_account_only_after_email_is_verified(self, check_code):
        self.user.email_verified = True
        self.user.save(update_fields=('email_verified',))
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        PhoneVerification.objects.create(
            user=self.user,
            code_hash='',
            provider_reference='termii-pin-id',
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_phone'),
            {'code': '012345'}
        )

        self.assertRedirects(response, reverse('home'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)
        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertFalse(PhoneVerification.objects.filter(user=self.user).exists())
        check_code.assert_called_once_with('termii-pin-id', '012345')

    @patch('users.views.check_phone_verification_code', return_value=True)
    def test_phone_code_alone_does_not_activate_account(self, check_code):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        PhoneVerification.objects.create(
            user=self.user,
            code_hash='',
            provider_reference='termii-pin-id',
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_phone'),
            {'code': '012345'}
        )

        self.assertRedirects(response, reverse('verification_pending'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)
        self.assertFalse(self.user.email_verified)
        self.assertFalse(self.user.is_active)
        check_code.assert_called_once_with('termii-pin-id', '012345')

    def test_expired_phone_code_cannot_verify_number(self):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        PhoneVerification.objects.create(
            user=self.user,
            code_hash='',
            provider_reference='termii-pin-id',
            expires_at=timezone.now() - timedelta(seconds=1),
            last_sent_at=timezone.now() - timedelta(minutes=11),
        )

        response = self.client.post(
            reverse('verify_phone'),
            {'code': '012345'}
        )

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.phone_verified)
        self.assertFalse(self.user.is_active)
        self.assertContains(response, 'That code has expired.')

    @patch('users.views.check_phone_verification_code', return_value=False)
    def test_incorrect_phone_code_is_counted_and_account_remains_inactive(self, check_code):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        verification = PhoneVerification.objects.create(
            user=self.user,
            code_hash='',
            provider_reference='termii-pin-id',
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        response = self.client.post(
            reverse('verify_phone'),
            {'code': '999999'}
        )

        self.assertEqual(response.status_code, 200)
        verification.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(verification.failed_attempts, 1)
        self.assertFalse(self.user.phone_verified)
        self.assertFalse(self.user.is_active)
        self.assertContains(response, 'That code is incorrect.')
        check_code.assert_called_once_with('termii-pin-id', '999999')

    @patch('users.views.check_phone_verification_code', return_value=False)
    def test_phone_code_is_locked_after_five_incorrect_attempts(self, check_code):
        session = self.client.session
        session[PENDING_VERIFICATION_SESSION_KEY] = self.user.pk
        session.save()
        PhoneVerification.objects.create(
            user=self.user,
            code_hash='',
            provider_reference='termii-pin-id',
            expires_at=timezone.now() + timedelta(minutes=10),
            last_sent_at=timezone.now(),
        )

        for _ in range(5):
            self.client.post(reverse('verify_phone'), {'code': '999999'})

        response = self.client.post(
            reverse('verify_phone'),
            {'code': '012345'}
        )

        self.user.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertFalse(self.user.phone_verified)
        self.assertFalse(self.user.is_active)
        self.assertContains(response, 'Too many incorrect attempts.')
        self.assertEqual(check_code.call_count, 5)


class TermiiOtpIntegrationTests(TestCase):
    @override_settings(
        TERMII_API_KEY='test-api-key',
        TERMII_API_BASE_URL='https://api.ng.termii.com',
        TERMII_SENDER_ID='AssetLink',
    )
    @patch('users.verification.requests.post')
    def test_starts_sms_verification_through_termii(self, post):
        from .verification import send_phone_verification_code

        post.return_value.json.return_value = {'pinId': 'termii-pin-id'}

        pin_id = send_phone_verification_code('+254712345678')

        args, kwargs = post.call_args
        self.assertEqual(pin_id, 'termii-pin-id')
        self.assertEqual(
            args[0],
            'https://api.ng.termii.com/api/sms/otp/send',
        )
        self.assertEqual(kwargs['json']['api_key'], 'test-api-key')
        self.assertEqual(kwargs['json']['to'], '254712345678')
        self.assertEqual(kwargs['json']['from'], 'AssetLink')
        self.assertEqual(kwargs['json']['channel'], 'generic')
        self.assertEqual(kwargs['json']['pin_length'], 6)
        self.assertEqual(kwargs['json']['pin_attempts'], 5)
        self.assertEqual(kwargs['json']['pin_time_to_live'], 10)
        self.assertEqual(kwargs['timeout'], 10)

    @override_settings(
        TERMII_API_KEY='test-api-key',
        TERMII_API_BASE_URL='https://api.ng.termii.com',
    )
    @patch('users.verification.requests.post')
    def test_checks_sms_code_using_termii_result(self, post):
        from .verification import check_phone_verification_code

        post.return_value.json.return_value = {'verified': 'True'}

        self.assertTrue(check_phone_verification_code('termii-pin-id', '123456'))

        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://api.ng.termii.com/api/sms/otp/verify')
        self.assertEqual(
            kwargs['json'],
            {
                'api_key': 'test-api-key',
                'pin_id': 'termii-pin-id',
                'pin': '123456',
            },
        )

    @override_settings(
        TERMII_API_KEY='test-api-key',
        TERMII_API_BASE_URL='https://api.ng.termii.com',
    )
    @patch('users.verification.requests.post')
    def test_wrong_sms_code_is_rejected_by_termii(self, post):
        from .verification import check_phone_verification_code

        post.return_value.json.return_value = {'verified': 'False'}

        self.assertFalse(check_phone_verification_code('termii-pin-id', '999999'))


class AuthenticationPageLinkTests(TestCase):

    def test_login_links_to_terms_and_terms_title_identifies_page(self):
        login_response = self.client.get(reverse('login'))
        register_response = self.client.get(reverse('register'))
        terms_response = self.client.get(reverse('terms'))
        privacy_response = self.client.get(reverse('privacy'))

        self.assertContains(
            login_response,
            f'href="{reverse("terms")}"'
        )
        self.assertContains(login_response, 'placeholder="Enter your username"')
        self.assertContains(login_response, 'placeholder="Enter your password"')
        self.assertContains(
            login_response,
            'data-password-toggle="id_password"',
        )
        self.assertContains(
            login_response,
            'class="forgot-password-link"',
        )
        self.assertContains(register_response, 'placeholder="you@example.com"')
        self.assertContains(
            register_response,
            'data-password-toggle="id_password1"',
        )
        self.assertContains(
            register_response,
            'data-password-toggle="id_password2"',
        )
        self.assertContains(register_response, 'password-validation-help')
        self.assertContains(
            terms_response,
            '<title>Terms &amp; Conditions | AssetLinkAfrica</title>',
            html=True
        )
        self.assertContains(
            terms_response,
            f'href="{reverse("login")}"'
        )
        self.assertContains(terms_response, 'href="/static/css/pages.css"')
        self.assertContains(privacy_response, 'href="/static/css/pages.css"')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_email_resets_account_password(self):
        user = User.objects.create_user(
            username='reset-user',
            email='reset@example.com',
            password='Old-complex-password-948!',
        )

        response = self.client.post(
            reverse('password_reset'),
            {'email': user.email},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(user.email, mail.outbox[0].recipients())
        reset_path = re.search(
            r'(/users/password-reset/confirm/[^/\s]+/[^/\s]+/)',
            mail.outbox[0].body,
        )
        self.assertIsNotNone(reset_path)

        response = self.client.get(reset_path.group(1))
        self.assertEqual(response.status_code, 302)
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            response.request['PATH_INFO'],
            {
                'new_password1': 'New-complex-password-948!',
                'new_password2': 'New-complex-password-948!',
            },
        )

        self.assertRedirects(response, reverse('password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('New-complex-password-948!'))
        self.assertFalse(user.check_password('Old-complex-password-948!'))

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset_response_does_not_disclose_unknown_email(self):
        response = self.client.post(
            reverse('password_reset'),
            {'email': 'unknown@example.com'},
        )

        self.assertRedirects(response, reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(
            self.client.get(reverse('password_reset_done')),
            'If an active account exists for that email address',
        )
