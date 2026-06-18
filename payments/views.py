import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from bookings.models import Booking

from .models import Payment


@login_required
def checkout(request, id):

    booking = get_object_or_404(Booking, id=id, user=request.user)

    if booking.status == "approved":
        messages.info(request, "This booking has already been paid.")
        return redirect("payment_success")

    if request.method == "POST":

        payment_method = request.POST.get("payment_method")

        Payment.objects.create(
            booking=booking,
            amount=booking.listing.price,
            payment_method=payment_method,
            transaction_id=str(uuid.uuid4()),
            is_paid=True,
        )

        booking.status = "approved"
        booking.listing.status = "booked"
        booking.listing.save()
        booking.save()

        return redirect("payment_success")

    return render(request, "payments/checkout.html", {"booking": booking})


@login_required
def payment_success(request):

    return render(request, "payments/payment-success.html")
