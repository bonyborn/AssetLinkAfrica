from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from listings.models import Listing
from bookings.models import Booking


@login_required
def dashboard(request):

    listings = Listing.objects.filter(
        owner=request.user
    )

    bookings = Booking.objects.filter(
        user=request.user
    )

    context = {

        'listings': listings,

        'bookings': bookings,

        'listing_count': listings.count(),

        'booking_count': bookings.count()

    }

    return render(
        request,
        'dashboard/dashboard.html',
        context
    )
