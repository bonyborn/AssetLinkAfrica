import uuid

from django.shortcuts import render
from django.shortcuts import redirect

from bookings.models import Booking

from .models import Payment


def checkout(request, id):

    booking = Booking.objects.get(id=id)

    if request.method == 'POST':

        payment_method = request.POST.get(
            'payment_method'
        )

        Payment.objects.create(

            booking=booking,

            amount=booking.listing.price,

            payment_method=payment_method,

            transaction_id=str(uuid.uuid4()),

            is_paid=True
        )

        booking.status = 'approved'

        booking.save()

        return redirect('payment_success')

    return render(
        request,
        'payments/checkout.html',
        {'booking': booking}
    )


def payment_success(request):

    return render(
        request,
        'payments/payment-success.html'
      )
