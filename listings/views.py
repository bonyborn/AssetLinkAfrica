from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.decorators import login_required

from .models import Listing, ListingImage, Subscription, SubscriptionPlan
from .forms import ListingForm


def listings(request):

    listings = Listing.objects.all()

    query = request.GET.get('q')

    category = request.GET.get('category')

    location = request.GET.get('location')

    if query:
        listings = listings.filter(
            title__icontains=query
        )

    if category:
        listings = listings.filter(
            category=category
        )

    if location:
        listings = listings.filter(
            location__icontains=location
        )

    context = {
        'listings': listings
    }

    return render(
        request,
        'listings/listings.html',
        context
    )


@login_required
def create_listing(request):

    if request.method == 'POST':
        form = ListingForm(
            request.POST,
            request.FILES
        )
        if form.is_valid():
            with transaction.atomic():
                user = get_user_model().objects.select_for_update().get(
                    pk=request.user.pk
                )
                subscription = Subscription.active_for_user(user)
                plan = (
                    subscription.plan
                    if subscription
                    else SubscriptionPlan.objects.get(code='basic', is_active=True)
                )
                listing_count = Listing.objects.filter(owner=user).count()
                if (
                    plan.maximum_listings is not None
                    and listing_count >= plan.maximum_listings
                ):
                    form.add_error(
                        None,
                        f'The {plan.get_code_display()} plan allows up to '
                        f'{plan.maximum_listings} listing(s). Upgrade your plan '
                        'to publish more assets.',
                    )
                else:
                    listing = form.save(commit=False)
                    listing.owner = user
                    listing.save()
                    ListingImage.objects.bulk_create([
                        ListingImage(listing=listing, image=image)
                        for image in form.cleaned_data['gallery_images']
                    ])
                    messages.success(request, 'Your listing has been published.')
                    return redirect('listings')

    else:
        form = ListingForm(initial={
            'contact_name': request.user.get_full_name() or request.user.username,
            'contact_phone': request.user.phone_number,
            'contact_email': request.user.email,
        })

    return render(
        request,
        'listings/create.html',
        {'form': form}
    )


def details(request, id):

    listing = get_object_or_404(
        Listing.objects.prefetch_related('images'),
        id=id
    )

    return render(
        request,
        'listings/details.html',
        {'listing': listing}
    )
