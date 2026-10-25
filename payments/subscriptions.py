from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from listings.models import Subscription

from .models import SubscriptionPayment


def activate_subscription_payment(payment_id, receipt_number=''):
    with transaction.atomic():
        payment = SubscriptionPayment.objects.select_for_update().get(
            pk=payment_id
        )
        if payment.status == SubscriptionPayment.STATUS_PAID:
            return payment
        if payment.status != SubscriptionPayment.STATUS_PENDING:
            raise ValueError('Only pending subscription payments can be verified.')

        user = get_user_model().objects.select_for_update().get(
            pk=payment.user_id
        )
        starts_at = timezone.now()
        subscription = (
            Subscription.objects.select_for_update()
            .filter(
                user=user,
                status='active',
                starts_at__lte=starts_at,
            )
            .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=starts_at))
            .first()
        )
        if subscription and subscription.plan_id == payment.plan_id:
            subscription.ends_at = (
                subscription.ends_at or starts_at
            ) + relativedelta(months=1)
            subscription.save(update_fields=('ends_at',))
        else:
            Subscription.objects.select_for_update().filter(
                user=user,
                status='active',
            ).update(status='cancelled')
            subscription = Subscription.objects.create(
                user=user,
                plan=payment.plan,
                status='active',
                starts_at=starts_at,
                ends_at=starts_at + relativedelta(months=1),
            )

        payment.status = SubscriptionPayment.STATUS_PAID
        payment.subscription = subscription
        payment.receipt_number = receipt_number or None
        payment.result_description = 'Subscription payment confirmed.'
        payment.save(update_fields=(
            'status',
            'subscription',
            'receipt_number',
            'result_description',
            'updated_at',
        ))
        return payment
