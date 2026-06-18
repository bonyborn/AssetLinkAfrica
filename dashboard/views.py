from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from bookings.models import Booking
from listings.models import Listing
from payments.models import Payment


@login_required
def dashboard(request):

    listings = Listing.objects.filter(owner=request.user)

    bookings = Booking.objects.filter(user=request.user)

    payments = Payment.objects.filter(booking__user=request.user)

    context = {
        "listings": listings,
        "bookings": bookings,
        "payments": payments,
        "listing_count": listings.count(),
        "booking_count": bookings.count(),
        "payment_count": payments.count(),
    }

    return render(request, "dashboard/dashboard.html", context)
