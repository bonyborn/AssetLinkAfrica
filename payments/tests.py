import json
import hashlib
import hmac
import time
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from django.test import TestCase, override_settings
from django.urls import reverse

from bookings.models import Booking
from listings.models import Listing, Subscription, SubscriptionPlan
from users.models import User

from .models import Payment, SubscriptionPayment
from .mpesa import initiate_stk_push
from .subscriptions import activate_subscription_payment
from .admin import SubscriptionPaymentAdmin


class CheckoutTemplateTests(TestCase):

    def setUp(self):
        owner = User.objects.create_user(
            username='checkout-owner',
            password='test-password-123'
        )
        self.customer = User.objects.create_user(
            username='checkout-customer',
            password='test-password-123',
            phone_number='+254712345678',
        )
        listing = Listing.objects.create(
            owner=owner,
            title='Checkout test car',
            description='A test listing for checkout.',
            category='car',
            price='2100000.00',
            location='Nairobi',
            image='listings/checkout-test.jpg'
        )
        self.booking = Booking.objects.create(
            user=self.customer,
            listing=listing
        )

    def test_checkout_requires_login(self):
        response = self.client.get(reverse('checkout', args=[self.booking.id]))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('checkout', args=[self.booking.id])}"
        )

    def test_checkout_shows_booking_summary_and_mpesa_phone_field(self):
        self.client.force_login(self.customer)
        response = self.client.get(
            reverse('checkout', args=[self.booking.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/checkout.html')
        self.assertContains(response, self.booking.listing.title)
        self.assertContains(response, 'name="phone_number"')
        self.assertContains(response, 'M-Pesa phone number')
        self.assertContains(response, 'We never ask for your M-Pesa PIN.')

    def test_customer_cannot_checkout_another_users_booking(self):
        other_user = User.objects.create_user(
            username='another-customer',
            password='test-password-123',
        )
        self.client.force_login(other_user)

        response = self.client.get(reverse('checkout', args=[self.booking.id]))

        self.assertEqual(response.status_code, 404)

    @patch('payments.views.initiate_stk_push')
    def test_checkout_starts_pending_stk_push(self, initiate_stk_push):
        def accept_prompt(payment, phone_number):
            payment.checkout_request_id = 'ws_CO_123'
            payment.save(update_fields=('checkout_request_id',))
            return payment

        initiate_stk_push.side_effect = accept_prompt
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse('checkout', args=[self.booking.id]),
            {'phone_number': '+254712345678'},
        )
        payment = Payment.objects.get(booking=self.booking)

        self.assertRedirects(
            response,
            reverse('payment_success', args=[payment.id]),
        )
        self.assertEqual(payment.status, Payment.STATUS_PENDING)
        self.assertEqual(payment.phone_number, '254712345678')
        self.assertEqual(self.booking.status, 'pending')
        initiate_stk_push.assert_called_once_with(payment, '254712345678')

    @patch('payments.views.initiate_stk_push')
    def test_invalid_phone_does_not_create_or_initiate_payment(self, initiate_stk_push):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse('checkout', args=[self.booking.id]),
            {'phone_number': 'not-a-phone'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid Kenyan M-Pesa number')
        self.assertFalse(Payment.objects.exists())
        initiate_stk_push.assert_not_called()

    @override_settings(
        MPESA_CONSUMER_KEY='',
        MPESA_CONSUMER_SECRET='',
        MPESA_SHORTCODE='',
        MPESA_PASSKEY='',
        MPESA_CALLBACK_URL='',
    )
    def test_missing_gateway_configuration_never_confirms_payment(self):
        self.client.force_login(self.customer)

        with self.assertLogs('payments.views', level='ERROR'):
            response = self.client.post(
                reverse('checkout', args=[self.booking.id]),
                {'phone_number': '+254712345678'},
            )

        payment = Payment.objects.get(booking=self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'M-Pesa is not available right now')
        self.assertEqual(payment.status, Payment.STATUS_FAILED)
        self.assertEqual(self.booking.status, 'pending')

    def create_pending_payment(self):
        return Payment.objects.create(
            booking=self.booking,
            amount=self.booking.listing.price,
            payment_method='mpesa',
            transaction_id='test-transaction',
            status=Payment.STATUS_PENDING,
            phone_number='254712345678',
            checkout_request_id='ws_CO_123',
        )

    def test_valid_callback_marks_payment_and_booking_paid(self):
        payment = self.create_pending_payment()
        callback = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': payment.checkout_request_id,
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 2100000},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'QGH123ABC'},
                            {'Name': 'PhoneNumber', 'Value': 254712345678},
                        ],
                    },
                },
            },
        }

        response = self.client.post(
            reverse('mpesa_callback'),
            data=json.dumps(callback),
            content_type='application/json',
        )
        payment.refresh_from_db()
        self.booking.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.STATUS_PAID)
        self.assertEqual(payment.receipt_number, 'QGH123ABC')
        self.assertEqual(self.booking.status, 'approved')

    def test_failed_callback_keeps_booking_unconfirmed(self):
        payment = self.create_pending_payment()
        callback = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': payment.checkout_request_id,
                    'ResultCode': 1032,
                    'ResultDesc': 'Request cancelled by user',
                },
            },
        }

        response = self.client.post(
            reverse('mpesa_callback'),
            data=json.dumps(callback),
            content_type='application/json',
        )
        payment.refresh_from_db()
        self.booking.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, Payment.STATUS_FAILED)
        self.assertEqual(self.booking.status, 'rejected')
        self.booking.listing.refresh_from_db()
        self.assertEqual(self.booking.listing.status, 'available')

    def test_callback_with_mismatched_amount_is_rejected(self):
        payment = self.create_pending_payment()
        callback = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': payment.checkout_request_id,
                    'ResultCode': 0,
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 1},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'QGH123ABC'},
                            {'Name': 'PhoneNumber', 'Value': 254712345678},
                        ],
                    },
                },
            },
        }

        response = self.client.post(
            reverse('mpesa_callback'),
            data=json.dumps(callback),
            content_type='application/json',
        )
        payment.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

    @override_settings(
        MPESA_API_BASE_URL='https://sandbox.safaricom.co.ke',
        MPESA_CONSUMER_KEY='test-key',
        MPESA_CONSUMER_SECRET='test-secret',
        MPESA_SHORTCODE='174379',
        MPESA_PASSKEY='test-passkey',
        MPESA_CALLBACK_URL='https://example.com/payments/mpesa/callback/',
        MPESA_TRANSACTION_TYPE='CustomerPayBillOnline',
    )
    @patch('payments.mpesa.requests.post')
    @patch('payments.mpesa.requests.get')
    def test_stk_push_uses_daraja_and_saves_request_id(self, mock_get, mock_post):
        payment = self.create_pending_payment()
        mock_get.return_value.json.return_value = {'access_token': 'test-access-token'}
        mock_post.return_value.json.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'ws_CO_new',
            'CustomerMessage': 'Success. Request accepted for processing',
        }

        initiate_stk_push(payment, payment.phone_number)

        self.assertEqual(mock_get.call_args.args[0], (
            'https://sandbox.safaricom.co.ke/oauth/v1/generate'
        ))
        self.assertEqual(
            mock_post.call_args.kwargs['headers']['Authorization'],
            'Bearer test-access-token',
        )
        self.assertEqual(mock_post.call_args.kwargs['json']['Amount'], 2100000)
        self.assertLessEqual(
            len(mock_post.call_args.kwargs['json']['AccountReference']),
            12,
        )
        self.assertLessEqual(
            len(mock_post.call_args.kwargs['json']['TransactionDesc']),
            13,
        )
        self.assertEqual(
            mock_post.call_args.kwargs['json']['CallBackURL'],
            'https://example.com/payments/mpesa/callback/',
        )
        payment.refresh_from_db()
        self.assertEqual(payment.checkout_request_id, 'ws_CO_new')
        self.assertEqual(payment.status, Payment.STATUS_PENDING)

    def test_payment_status_page_requires_ownership(self):
        payment = self.create_pending_payment()
        other_user = User.objects.create_user(
            username='payment-outsider',
            password='test-password-123',
        )
        self.client.force_login(other_user)

        response = self.client.get(
            reverse('payment_success', args=[payment.id])
        )

        self.assertEqual(response.status_code, 404)

    def test_payment_status_page_only_shows_success_after_confirmation(self):
        payment = self.create_pending_payment()
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse('payment_success', args=[payment.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Approve the M-Pesa prompt')
        self.assertNotContains(response, 'Payment successful')


class SubscriptionCheckoutTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='subscription-customer',
            email='subscription@example.com',
            password='test-password-123',
            phone_number='+254712345678',
        )
        self.plan = SubscriptionPlan.objects.get(code='premium')
        self.client.force_login(self.user)

    def start_checkout(self, payment_method, **fields):
        return self.client.post(
            reverse('subscription_checkout', args=[self.plan.code]),
            {'payment_method': payment_method, **fields},
        )

    def create_payment(self, payment_method='mpesa', **fields):
        defaults = {
            'user': self.user,
            'plan': self.plan,
            'amount': self.plan.monthly_price,
            'payment_method': payment_method,
            'transaction_id': f'subscription-{SubscriptionPayment.objects.count() + 1}',
        }
        defaults.update(fields)
        return SubscriptionPayment.objects.create(**defaults)

    @staticmethod
    def stripe_signature(payload, secret):
        timestamp = str(int(time.time()))
        signed_payload = f'{timestamp}.{payload}'.encode()
        signature = hmac.new(
            secret.encode(),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        return f't={timestamp},v1={signature}'

    def test_subscription_plans_page_shows_seeded_monthly_tiers(self):
        response = self.client.get(reverse('subscription_plans'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Premium')
        self.assertContains(response, 'KES 3499/month')
        self.assertContains(response, 'Featured')
        self.assertContains(response, 'KES 4999/month')

    def test_subscription_checkout_shows_payment_method_cards(self):
        response = self.client.get(
            reverse('subscription_checkout', args=[self.plan.code])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="form-group payment-methods"')
        self.assertContains(response, 'value="mpesa"')
        self.assertContains(response, 'value="card"')
        self.assertContains(response, 'value="bank"')
        self.assertContains(response, 'class="payment-method-icon mpesa-icon"')
        self.assertContains(response, 'class="payment-method-icon card-icon"')
        self.assertContains(response, 'class="payment-method-icon bank-icon"')

    @override_settings(
        BANK_TRANSFER_BANK_NAME='AssetLink Bank',
        BANK_TRANSFER_ACCOUNT_NAME='AssetLink Africa Ltd',
        BANK_TRANSFER_ACCOUNT_NUMBER='12345678',
        BANK_TRANSFER_BRANCH='Nairobi',
        BANK_TRANSFER_SWIFT_CODE='ALAKE01',
    )
    def test_bank_transfer_stays_pending_until_admin_verifies_it(self):
        response = self.start_checkout(
            'bank',
            bank_transfer_reference='BANK-REF-001',
        )
        payment = SubscriptionPayment.objects.get(user=self.user)

        self.assertRedirects(
            response,
            reverse('subscription_payment_status', args=[payment.id]),
        )
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)
        self.assertEqual(payment.bank_transfer_reference, 'BANK-REF-001')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

        duplicate_response = self.start_checkout(
            'bank',
            bank_transfer_reference='BANK-REF-002',
        )
        self.assertRedirects(
            duplicate_response,
            reverse('subscription_payment_status', args=[payment.id]),
        )
        self.assertEqual(
            SubscriptionPayment.objects.filter(user=self.user).count(),
            1,
        )

        activate_subscription_payment(payment.pk)
        payment.refresh_from_db()
        payment.subscription.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.subscription.plan, self.plan)
        self.assertEqual(
            payment.subscription.ends_at,
            payment.subscription.starts_at + relativedelta(months=1),
        )

    def test_bank_transfer_requires_configured_recipient_details(self):
        response = self.start_checkout(
            'bank',
            bank_transfer_reference='BANK-REF-002',
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'recipient details are configured')
        self.assertFalse(SubscriptionPayment.objects.exists())

    def test_same_plan_payment_renews_period_without_duplicate_subscription(self):
        first_payment = self.create_payment('bank')
        activate_subscription_payment(first_payment.pk)
        first_payment.refresh_from_db()
        first_payment.subscription.refresh_from_db()
        initial_end = first_payment.subscription.ends_at

        renewal = self.create_payment('bank')
        activate_subscription_payment(renewal.pk)
        renewal.refresh_from_db()

        self.assertEqual(renewal.subscription_id, first_payment.subscription_id)
        self.assertEqual(
            renewal.subscription.ends_at,
            initial_end + relativedelta(months=1),
        )
        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)

    @patch('payments.views.initiate_stk_push')
    def test_mpesa_checkout_sends_stk_prompt_and_waits_for_callback(self, initiate_stk_push):
        def accept_prompt(payment, _phone_number, **_kwargs):
            payment.checkout_request_id = 'ws_CO_subscription_start'
            payment.save(update_fields=('checkout_request_id',))
            return payment

        initiate_stk_push.side_effect = accept_prompt

        response = self.start_checkout(
            'mpesa',
            phone_number='+254712345678',
        )
        payment = SubscriptionPayment.objects.get(user=self.user)

        self.assertRedirects(
            response,
            reverse('subscription_payment_status', args=[payment.pk]),
        )
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)
        self.assertEqual(payment.phone_number, '254712345678')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())
        initiate_stk_push.assert_called_once_with(
            payment,
            '254712345678',
            transaction_description='Subscription',
        )

    @override_settings(
        STRIPE_SECRET_KEY='sk_test_example',
        STRIPE_WEBHOOK_SECRET='whsec_test_example',
    )
    @patch('payments.views.stripe.checkout.Session.create')
    def test_card_checkout_redirects_to_stripe_without_activating_plan(self, create_session):
        create_session.return_value = {
            'id': 'cs_test_subscription',
            'url': 'https://checkout.stripe.com/c/pay/cs_test_subscription',
        }

        response = self.start_checkout('card')
        payment = SubscriptionPayment.objects.get(user=self.user)

        self.assertRedirects(
            response,
            'https://checkout.stripe.com/c/pay/cs_test_subscription',
            fetch_redirect_response=False,
        )
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)
        self.assertEqual(payment.amount, Decimal('3499.00'))
        self.assertEqual(payment.stripe_session_id, 'cs_test_subscription')
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())
        request_data = create_session.call_args.kwargs
        self.assertEqual(request_data['line_items'][0]['price_data']['currency'], 'kes')
        self.assertEqual(request_data['line_items'][0]['price_data']['unit_amount'], 349900)
        self.assertEqual(
            request_data['metadata']['subscription_payment_id'],
            str(payment.pk),
        )

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test_example')
    def test_invalid_stripe_signature_does_not_activate_subscription(self):
        response = self.client.post(
            reverse('stripe_webhook'),
            data='{}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test_example')
    def test_stripe_webhook_verifies_and_activates_subscription_once(self):
        payment = self.create_payment(
            'card',
            stripe_session_id='cs_test_paid',
        )
        event = json.dumps({
            'id': 'evt_subscription_paid',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_paid',
                    'mode': 'payment',
                    'payment_status': 'paid',
                    'amount_total': 349900,
                    'currency': 'kes',
                    'payment_intent': 'pi_test_paid',
                    'metadata': {
                        'subscription_payment_id': str(payment.pk),
                        'transaction_id': payment.transaction_id,
                        'user_id': str(self.user.pk),
                        'plan_id': str(self.plan.pk),
                    },
                },
            },
        })
        signature = self.stripe_signature(event, 'whsec_test_example')

        for _ in range(2):
            response = self.client.post(
                reverse('stripe_webhook'),
                data=event,
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE=signature,
            )
            self.assertEqual(response.status_code, 200)

        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test_paid')
        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)

    @override_settings(STRIPE_WEBHOOK_SECRET='whsec_test_example')
    def test_stripe_webhook_rejects_mismatched_amount(self):
        payment = self.create_payment('card', stripe_session_id='cs_test_wrong_amount')
        event = json.dumps({
            'id': 'evt_subscription_wrong_amount',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': payment.stripe_session_id,
                    'mode': 'payment',
                    'payment_status': 'paid',
                    'amount_total': 1,
                    'currency': 'kes',
                    'metadata': {
                        'subscription_payment_id': str(payment.pk),
                        'transaction_id': payment.transaction_id,
                        'user_id': str(self.user.pk),
                        'plan_id': str(self.plan.pk),
                    },
                },
            },
        })
        signature = self.stripe_signature(event, 'whsec_test_example')

        response = self.client.post(
            reverse('stripe_webhook'),
            data=event,
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE=signature,
        )

        payment.refresh_from_db()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PENDING)
        self.assertFalse(Subscription.objects.filter(user=self.user).exists())

    def test_admin_can_verify_a_bank_transfer(self):
        payment = self.create_payment(
            'bank',
            bank_transfer_reference='ADMIN-VERIFY-001',
        )
        admin_user = User.objects.create_superuser(
            username='subscription-admin',
            email='admin@example.com',
            password='test-password-123',
        )
        request = RequestFactory().post('/admin/')
        SessionMiddleware(lambda _request: None).process_request(request)
        request.user = admin_user
        request._messages = FallbackStorage(request)
        model_admin = SubscriptionPaymentAdmin(
            SubscriptionPayment,
            admin.site,
        )

        model_admin.verify_bank_transfers(
            request,
            SubscriptionPayment.objects.filter(pk=payment.pk),
        )

        payment.refresh_from_db()
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.subscription.plan, self.plan)

    def test_mpesa_callback_activates_verified_subscription_payment(self):
        payment = self.create_payment(
            'mpesa',
            phone_number='254712345678',
            checkout_request_id='ws_CO_subscription',
        )
        callback = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': payment.checkout_request_id,
                    'ResultCode': 0,
                    'ResultDesc': 'The service request is processed successfully',
                    'CallbackMetadata': {
                        'Item': [
                            {'Name': 'Amount', 'Value': 3499},
                            {'Name': 'MpesaReceiptNumber', 'Value': 'SUB123ABC'},
                            {'Name': 'PhoneNumber', 'Value': 254712345678},
                        ],
                    },
                },
            },
        }

        response = self.client.post(
            reverse('mpesa_callback'),
            data=json.dumps(callback),
            content_type='application/json',
        )
        payment.refresh_from_db()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payment.status, SubscriptionPayment.STATUS_PAID)
        self.assertEqual(payment.receipt_number, 'SUB123ABC')
        self.assertEqual(payment.subscription.plan, self.plan)
        self.assertEqual(Subscription.objects.filter(user=self.user).count(), 1)
