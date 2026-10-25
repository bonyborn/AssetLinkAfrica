import json
import logging
import uuid
from urllib.parse import urlparse

import requests
import stripe
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db import IntegrityError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from bookings.models import Booking
from listings.models import Subscription, SubscriptionPlan

from .forms import MpesaCheckoutForm
from .models import Payment, SubscriptionPayment
from .mpesa import (
    MpesaError,
    callback_amount_matches,
    callback_metadata,
    initiate_stk_push,
    normalize_phone_number,
)
from .subscription_forms import SubscriptionCheckoutForm
from .subscriptions import activate_subscription_payment

logger = logging.getLogger(__name__)

_BANK_TRANSFER_SETTING_NAMES = (
    'BANK_TRANSFER_BANK_NAME',
    'BANK_TRANSFER_ACCOUNT_NAME',
    'BANK_TRANSFER_ACCOUNT_NUMBER',
)


def _stripe_value(resource, key, default=None):
    try:
        return resource[key]
    except (KeyError, TypeError):
        return getattr(resource, key, default)


def _bank_transfer_details():
    return {
        'bank_name': settings.BANK_TRANSFER_BANK_NAME,
        'account_name': settings.BANK_TRANSFER_ACCOUNT_NAME,
        'account_number': settings.BANK_TRANSFER_ACCOUNT_NUMBER,
        'branch': settings.BANK_TRANSFER_BRANCH,
        'swift_code': settings.BANK_TRANSFER_SWIFT_CODE,
        'instructions': settings.BANK_TRANSFER_INSTRUCTIONS,
        'configured': all(
            getattr(settings, name, '')
            for name in _BANK_TRANSFER_SETTING_NAMES
        ),
    }


@login_required
def subscription_plans(request):
    return render(
        request,
        'payments/subscription-plans.html',
        {
            'plans': SubscriptionPlan.objects.filter(is_active=True),
            'active_subscription': Subscription.active_for_user(request.user),
        },
    )


@login_required
def subscription_checkout(request, plan_code):
    plan = get_object_or_404(
        SubscriptionPlan,
        code=plan_code,
        is_active=True,
    )
    if plan.code == 'basic' or plan.monthly_price <= 0:
        return redirect('subscription_plans')

    bank_transfer = _bank_transfer_details()
    form = SubscriptionCheckoutForm(
        request.POST or None,
        initial={'phone_number': request.user.phone_number},
    )
    listing_count = request.user.listings.count()
    if (
        plan.maximum_listings is not None
        and listing_count > plan.maximum_listings
    ):
        form.add_error(
            None,
            f'Your account currently has {listing_count} listings. '
            f'The {plan.get_code_display()} plan supports up to '
            f'{plan.maximum_listings}. Remove listings or choose a plan with a higher limit.',
        )
    if request.method == 'POST' and form.is_valid():
        payment_method = form.cleaned_data['payment_method']
        if payment_method == 'card' and not (
            settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET
        ):
            form.add_error(
                None,
                'Card payments are not configured. Please choose another method.',
            )
        elif payment_method == 'bank' and not bank_transfer['configured']:
            form.add_error(
                None,
                'Bank transfer is not available until recipient details are configured.',
            )
        else:
            try:
                with transaction.atomic():
                    user = get_user_model().objects.select_for_update().get(
                        pk=request.user.pk
                    )
                    pending_payment = SubscriptionPayment.objects.filter(
                        user=user,
                        status=SubscriptionPayment.STATUS_PENDING,
                    ).first()
                    if pending_payment:
                        return redirect(
                            'subscription_payment_status',
                            payment_id=pending_payment.pk,
                        )
                    payment = SubscriptionPayment.objects.create(
                        user=user,
                        plan=plan,
                        amount=plan.monthly_price,
                        payment_method=payment_method,
                        transaction_id=str(uuid.uuid4()),
                        phone_number=form.cleaned_data.get('phone_number', ''),
                        bank_transfer_reference=form.cleaned_data.get(
                            'bank_transfer_reference',
                            '',
                        ),
                    )
            except IntegrityError:
                pending_payment = SubscriptionPayment.objects.filter(
                    user=request.user,
                    status=SubscriptionPayment.STATUS_PENDING,
                ).first()
                if pending_payment is None:
                    raise
                return redirect(
                    'subscription_payment_status',
                    payment_id=pending_payment.pk,
                )

            if payment_method == 'bank':
                payment.result_description = (
                    'Transfer reference submitted; awaiting admin verification.'
                )
                payment.save(update_fields=('result_description', 'updated_at'))
                return redirect(
                    'subscription_payment_status',
                    payment_id=payment.id,
                )

            if payment_method == 'mpesa':
                try:
                    initiate_stk_push(
                        payment,
                        payment.phone_number,
                        transaction_description='Subscription',
                    )
                except ImproperlyConfigured:
                    logger.exception(
                        'M-Pesa subscription checkout is not configured for payment %s.',
                        payment.pk,
                    )
                    payment.status = SubscriptionPayment.STATUS_FAILED
                    payment.result_description = 'M-Pesa is not configured.'
                    payment.save(update_fields=('status', 'result_description', 'updated_at'))
                    form.add_error(
                        None,
                        'M-Pesa is not available right now. Please contact support.',
                    )
                except requests.HTTPError:
                    logger.exception(
                        'M-Pesa rejected subscription checkout for payment %s.',
                        payment.pk,
                    )
                    payment.status = SubscriptionPayment.STATUS_FAILED
                    payment.result_description = 'M-Pesa rejected the request.'
                    payment.save(update_fields=('status', 'result_description', 'updated_at'))
                    form.add_error(
                        None,
                        'M-Pesa rejected the request. Please try again or contact support.',
                    )
                except requests.RequestException:
                    logger.exception(
                        'Could not confirm whether M-Pesa received subscription payment %s.',
                        payment.pk,
                    )
                    payment.result_description = (
                        'M-Pesa did not respond. Check your phone before retrying.'
                    )
                    payment.save(update_fields=('result_description', 'updated_at'))
                    return redirect(
                        'subscription_payment_status',
                        payment_id=payment.id,
                    )
                except MpesaError as error:
                    logger.warning(
                        'M-Pesa rejected subscription payment %s: %s',
                        payment.pk,
                        error,
                    )
                    payment.status = SubscriptionPayment.STATUS_FAILED
                    payment.result_description = str(error)[:255]
                    payment.save(update_fields=('status', 'result_description', 'updated_at'))
                    form.add_error(None, str(error))
                else:
                    return redirect(
                        'subscription_payment_status',
                        payment_id=payment.id,
                    )
            else:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                try:
                    session = stripe.checkout.Session.create(
                        mode='payment',
                        payment_method_types=['card'],
                        customer_email=request.user.email or None,
                        line_items=[{
                            'price_data': {
                                'currency': 'kes',
                                'unit_amount': int(payment.amount * 100),
                                'product_data': {
                                    'name': f'{plan.get_code_display()} subscription',
                                    'description': 'One month of listing access.',
                                },
                            },
                            'quantity': 1,
                        }],
                        metadata={
                            'subscription_payment_id': str(payment.pk),
                            'transaction_id': payment.transaction_id,
                            'user_id': str(request.user.pk),
                            'plan_id': str(plan.pk),
                        },
                        success_url=request.build_absolute_uri(
                            reverse(
                                'subscription_payment_status',
                                args=[payment.pk],
                            )
                        ),
                        cancel_url=request.build_absolute_uri(
                            reverse(
                                'subscription_payment_status',
                                args=[payment.pk],
                            )
                        ),
                    )
                except stripe.StripeError:
                    logger.exception(
                        'Stripe Checkout session creation failed for subscription payment %s.',
                        payment.pk,
                    )
                    payment.status = SubscriptionPayment.STATUS_FAILED
                    payment.result_description = 'Card checkout could not be started.'
                    payment.save(update_fields=('status', 'result_description', 'updated_at'))
                    form.add_error(
                        None,
                        'Card checkout could not be started. Please try again or choose another method.',
                    )
                else:
                    checkout_url = _stripe_value(session, 'url')
                    session_id = _stripe_value(session, 'id')
                    parsed_url = urlparse(checkout_url or '')
                    if (
                        parsed_url.scheme != 'https'
                        or parsed_url.hostname != 'checkout.stripe.com'
                        or not isinstance(session_id, str)
                        or not session_id
                    ):
                        payment.status = SubscriptionPayment.STATUS_FAILED
                        payment.result_description = 'Stripe did not return a secure checkout URL.'
                        payment.save(update_fields=('status', 'result_description', 'updated_at'))
                        form.add_error(
                            None,
                            'Card checkout could not be started. Please choose another method.',
                        )
                    else:
                        payment.stripe_session_id = session_id
                        payment.save(update_fields=('stripe_session_id', 'updated_at'))
                        return redirect(checkout_url)

    return render(
        request,
        'payments/subscription-checkout.html',
        {
            'plan': plan,
            'form': form,
            'bank_transfer': bank_transfer,
            'stripe_configured': bool(
                settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET
            ),
        },
    )


@login_required
def subscription_payment_status(request, payment_id):
    payment = get_object_or_404(
        SubscriptionPayment.objects.select_related('plan', 'subscription'),
        pk=payment_id,
        user=request.user,
    )
    return render(
        request,
        'payments/subscription-payment-status.html',
        {
            'payment': payment,
            'bank_transfer': _bank_transfer_details(),
        },
    )


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        logger.error('Stripe webhook secret is not configured.')
        return JsonResponse({'error': 'Webhook is not configured.'}, status=503)

    signature = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(
            request.body,
            signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning('Rejected Stripe webhook with invalid payload or signature.')
        return JsonResponse({'error': 'Invalid webhook signature or payload.'}, status=400)

    event_type = event['type']
    session = event['data']['object']
    metadata = _stripe_value(session, 'metadata') or {}
    payment_id = _stripe_value(metadata, 'subscription_payment_id')
    if not payment_id:
        return JsonResponse({'received': True})

    with transaction.atomic():
        payment = (
            SubscriptionPayment.objects.select_for_update()
            .filter(
                pk=payment_id,
                stripe_session_id=_stripe_value(session, 'id'),
                transaction_id=_stripe_value(metadata, 'transaction_id'),
                user_id=_stripe_value(metadata, 'user_id'),
                plan_id=_stripe_value(metadata, 'plan_id'),
            )
            .first()
        )
    if payment is None:
        logger.warning('Stripe subscription webhook did not match a payment record.')
        return JsonResponse({'error': 'Unknown subscription payment.'}, status=404)

    if event_type == 'checkout.session.completed':
        if _stripe_value(session, 'payment_status') != 'paid':
            return JsonResponse({'received': True})
        expected_amount = int(payment.amount * 100)
        currency = _stripe_value(session, 'currency')
        if (
            _stripe_value(session, 'mode') != 'payment'
            or not isinstance(currency, str)
            or currency.lower() != 'kes'
            or _stripe_value(session, 'amount_total') != expected_amount
        ):
            logger.warning(
                'Rejected Stripe checkout with mismatched details for payment %s.',
                payment.pk,
            )
            return JsonResponse({'error': 'Payment details did not match.'}, status=400)

        payment_intent = _stripe_value(session, 'payment_intent')
        if isinstance(payment_intent, str):
            payment.stripe_payment_intent_id = payment_intent
            payment.save(update_fields=('stripe_payment_intent_id', 'updated_at'))
        try:
            activate_subscription_payment(payment.pk)
        except ValueError:
            logger.warning(
                'Ignored Stripe success event for non-pending subscription payment %s.',
                payment.pk,
            )
    elif event_type in (
        'checkout.session.expired',
        'checkout.session.async_payment_failed',
    ):
        SubscriptionPayment.objects.filter(
            pk=payment.pk,
            status=SubscriptionPayment.STATUS_PENDING,
        ).update(
            status=SubscriptionPayment.STATUS_FAILED,
            result_description='Stripe checkout expired or payment failed.',
            updated_at=timezone.now(),
        )

    return JsonResponse({'received': True})


@login_required
def checkout(request, id):
    booking = get_object_or_404(
        Booking.objects.select_related('listing'),
        id=id,
        user=request.user,
    )
    payment = Payment.objects.filter(booking=booking).first()
    if payment and payment.status == Payment.STATUS_PAID:
        return redirect('payment_success', payment_id=payment.id)
    if payment and payment.status == Payment.STATUS_PENDING:
        return redirect('payment_success', payment_id=payment.id)

    form = MpesaCheckoutForm(
        request.POST or None,
        initial={'phone_number': request.user.phone_number},
    )
    if request.method == 'POST' and form.is_valid():
        try:
            phone_number = normalize_phone_number(form.cleaned_data['phone_number'])
        except ValueError as error:
            form.add_error('phone_number', str(error))
        else:
            with transaction.atomic():
                booking = Booking.objects.select_for_update().get(
                    id=booking.id,
                    user=request.user,
                )
                payment, created = Payment.objects.select_for_update().get_or_create(
                    booking=booking,
                    defaults={
                        'amount': booking.listing.price,
                        'payment_method': 'mpesa',
                        'transaction_id': str(uuid.uuid4()),
                        'phone_number': phone_number,
                    },
                )
                if payment.status == Payment.STATUS_PAID:
                    return redirect('payment_success', payment_id=payment.id)
                if not created and payment.status == Payment.STATUS_PENDING:
                    return redirect('payment_success', payment_id=payment.id)

                payment.amount = booking.listing.price
                payment.payment_method = 'mpesa'
                payment.transaction_id = str(uuid.uuid4())
                payment.phone_number = phone_number
                payment.status = Payment.STATUS_PENDING
                payment.checkout_request_id = None
                payment.receipt_number = None
                payment.result_description = ''
                payment.save()

            try:
                initiate_stk_push(payment, phone_number)
            except ImproperlyConfigured:
                logger.exception('M-Pesa checkout is not configured.')
                payment.status = Payment.STATUS_FAILED
                payment.result_description = 'M-Pesa is not configured. Please contact support.'
                payment.save(update_fields=('status', 'result_description'))
                form.add_error(
                    None,
                    'M-Pesa is not available right now. Please contact support.',
                )
            except requests.HTTPError:
                logger.exception('M-Pesa rejected the checkout request.')
                payment.status = Payment.STATUS_FAILED
                payment.result_description = 'M-Pesa rejected the request. Please try again.'
                payment.save(update_fields=('status', 'result_description'))
                form.add_error(
                    None,
                    'M-Pesa rejected the request. Please try again or contact support.',
                )
            except requests.RequestException:
                logger.exception('Could not confirm whether M-Pesa received the checkout request.')
                payment.result_description = (
                    'M-Pesa did not respond. Check your phone and refresh this page. '
                    'Do not start another payment until this request is resolved.'
                )
                payment.save(update_fields=('result_description',))
                return redirect('payment_success', payment_id=payment.id)
            except MpesaError as error:
                logger.warning('M-Pesa rejected checkout for payment %s: %s', payment.pk, error)
                payment.status = Payment.STATUS_FAILED
                payment.result_description = str(error)[:255]
                payment.save(update_fields=('status', 'result_description'))
                form.add_error(None, str(error))
            else:
                return redirect('payment_success', payment_id=payment.id)

    return render(
        request,
        'payments/checkout.html',
        {'booking': booking, 'form': form},
    )


@login_required
def payment_success(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related('booking__listing'),
        id=payment_id,
        booking__user=request.user,
    )
    return render(
        request,
        'payments/payment-success.html',
        {'payment': payment},
    )


@csrf_exempt
@require_POST
def mpesa_callback(request):
    try:
        callback = json.loads(request.body)
        if not isinstance(callback, dict):
            raise ValueError('M-Pesa callback must be a JSON object.')
        checkout_request_id, result_code, stk_callback, metadata = callback_metadata(callback)
    except (ValueError, TypeError) as error:
        logger.warning('Rejected malformed M-Pesa callback: %s', error)
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid callback'}, status=400)

    with transaction.atomic():
        payment = (
            Payment.objects.select_for_update()
            .select_related('booking')
            .filter(checkout_request_id=checkout_request_id)
            .first()
        )
        subscription_payment = None
        if payment is None:
            subscription_payment = (
                SubscriptionPayment.objects.select_for_update()
                .filter(checkout_request_id=checkout_request_id)
                .first()
            )
        if payment is None and subscription_payment is None:
            logger.warning('Received M-Pesa callback for an unknown checkout request.')
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Unknown checkout request'}, status=404)
        if subscription_payment is not None:
            if subscription_payment.status == SubscriptionPayment.STATUS_PAID:
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Already processed'})
            if subscription_payment.status == SubscriptionPayment.STATUS_FAILED:
                return JsonResponse(
                    {'ResultCode': 1, 'ResultDesc': 'Payment is no longer pending'},
                    status=409,
                )

            if result_code != 0:
                subscription_payment.status = SubscriptionPayment.STATUS_FAILED
                subscription_payment.result_description = str(
                    stk_callback.get('ResultDesc') or 'M-Pesa payment was not completed.'
                )[:255]
                subscription_payment.save(update_fields=(
                    'status',
                    'result_description',
                    'updated_at',
                ))
                return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback accepted'})

            receipt_number = metadata.get('MpesaReceiptNumber')
            if (
                not callback_amount_matches(metadata.get('Amount'), subscription_payment.amount)
                or str(metadata.get('PhoneNumber')) != subscription_payment.phone_number
                or not isinstance(receipt_number, str)
                or not receipt_number
            ):
                logger.warning('Rejected M-Pesa callback with mismatched subscription payment details.')
                return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment details did not match'}, status=400)

            try:
                activate_subscription_payment(
                    subscription_payment.pk,
                    receipt_number=receipt_number,
                )
            except ValueError:
                logger.warning(
                    'Ignored M-Pesa success callback for non-pending subscription payment %s.',
                    subscription_payment.pk,
                )
                return JsonResponse(
                    {'ResultCode': 1, 'ResultDesc': 'Payment is no longer pending'},
                    status=409,
                )
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback accepted'})

        if payment.status == Payment.STATUS_PAID:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Already processed'})

        if result_code != 0:
            payment.status = Payment.STATUS_FAILED
            payment.result_description = str(
                stk_callback.get('ResultDesc') or 'M-Pesa payment was not completed.'
            )[:255]
            payment.save(update_fields=('status', 'result_description'))
            payment.booking.status = 'rejected'
            payment.booking.save(update_fields=('status',))
            payment.booking.listing.status = 'available'
            payment.booking.listing.save(update_fields=('status',))
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback accepted'})

        callback_phone = metadata.get('PhoneNumber')
        receipt_number = metadata.get('MpesaReceiptNumber')
        if (
            not callback_amount_matches(metadata.get('Amount'), payment.amount)
            or str(callback_phone) != payment.phone_number
            or not isinstance(receipt_number, str)
            or not receipt_number
        ):
            logger.warning('Rejected M-Pesa callback with mismatched payment details.')
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Payment details did not match'}, status=400)

        payment.status = Payment.STATUS_PAID
        payment.receipt_number = receipt_number
        payment.result_description = 'Payment confirmed by M-Pesa.'
        payment.save(update_fields=(
            'status',
            'receipt_number',
            'result_description',
        ))
        payment.booking.status = 'approved'
        payment.booking.save(update_fields=('status',))

    return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Callback accepted'})
