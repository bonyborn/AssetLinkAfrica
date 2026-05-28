from django.shortcuts import get_object_or_404
from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required

from listings.models import Listing

from .models import Booking


@login_required
def create_booking(request, id):

    listing = get_object_or_404(
        Listing,
        id=id
    )

    booking = Booking.objects.create(
        user=request.user,
        listing=listing
    )

    return redirect(
        'checkout',
        booking.id
    )
