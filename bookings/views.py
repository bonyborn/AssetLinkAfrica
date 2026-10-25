from django.shortcuts import get_object_or_404, redirect, render

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.db import transaction
from django.views.decorators.http import require_POST

from listings.models import Listing

from .models import Booking


@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(
        user=request.user
    ).select_related('listing').order_by('-created_at')

    return render(
        request,
        'bookings/bookings.html',
        {'bookings': bookings}
    )


@login_required
@require_POST
def create_booking(request, id):
    try:
        with transaction.atomic():
            listing = get_object_or_404(
                Listing.objects.select_for_update(),
                id=id
            )
            existing_booking = Booking.objects.filter(
                listing=listing,
                status__in=('pending', 'approved'),
            ).first()

            if listing.status != 'available' or existing_booking:
                if existing_booking and existing_booking.user_id == request.user.id:
                    return redirect('checkout', existing_booking.id)
                messages.warning(request, 'This asset is already booked.')
                return redirect('details', listing.id)

            booking = Booking.objects.create(
                user=request.user,
                listing=listing
            )
            listing.status = 'booked'
            listing.save(update_fields=('status',))
    except IntegrityError:
        existing_booking = Booking.objects.filter(
            listing_id=id,
            status__in=('pending', 'approved'),
        ).first()
        if existing_booking is None:
            raise
        if existing_booking.user_id == request.user.id:
            return redirect('checkout', existing_booking.id)
        messages.warning(request, 'This asset is already booked.')
        return redirect('details', id)

    return redirect(
        'checkout',
        booking.id
    )
