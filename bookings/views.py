from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from listings.models import Listing

from .models import Booking


@login_required
def create_booking(request, id):

    listing = get_object_or_404(Listing, id=id)

    if listing.owner == request.user:
        messages.error(request, "You cannot book your own listing.")
        return redirect("details", id=listing.id)

    if listing.status != "available":
        messages.error(request, "This listing is not available for booking.")
        return redirect("details", id=listing.id)

    booking = Booking.objects.create(user=request.user, listing=listing)

    listing.status = "booked"
    listing.save()

    return redirect("checkout", booking.id)
