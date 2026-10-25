from django.urls import path
from . import views


urlpatterns = [

    path(
        'subscriptions/',
        views.subscription_plans,
        name='subscription_plans'
    ),

    path(
        'subscriptions/<slug:plan_code>/checkout/',
        views.subscription_checkout,
        name='subscription_checkout'
    ),

    path(
        'subscriptions/<int:payment_id>/status/',
        views.subscription_payment_status,
        name='subscription_payment_status'
    ),

    path(
        'stripe/webhook/',
        views.stripe_webhook,
        name='stripe_webhook'
    ),

    path(
        'checkout/<int:id>/',
        views.checkout,
        name='checkout'
    ),

    path(
        'success/<int:payment_id>/',
        views.payment_success,
        name='payment_success'
    ),

    path(
        'mpesa/callback/',
        views.mpesa_callback,
        name='mpesa_callback'
    ),

]
