from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from listings.models import Listing, Subscription, SubscriptionPlan
from bookings.models import Booking


@login_required
def dashboard(request):

    listings = Listing.objects.filter(
        owner=request.user
    )

    bookings = Booking.objects.filter(
        user=request.user
    )
    active_subscription = Subscription.active_for_user(request.user)
    listing_plan = (
        active_subscription.plan
        if active_subscription
        else SubscriptionPlan.objects.get(code='basic', is_active=True)
    )

    context = {

        'listings': listings,

        'bookings': bookings,

        'listing_count': listings.count(),

        'booking_count': bookings.count(),

        'active_subscription': active_subscription,

        'listing_plan': listing_plan,

    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )
