from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from django.contrib.auth.decorators import login_required

from .models import Listing
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

            listing = form.save(commit=False)

            listing.owner = request.user

            listing.save()

            return redirect('listings')

    else:

        form = ListingForm()

    return render(
        request,
        'listings/create.html',
        {'form': form}
    )


def details(request, id):

    listing = get_object_or_404(
        Listing,
        id=id
    )

    return render(
        request,
        'listings/details.html',
        {'listing': listing}
  )
