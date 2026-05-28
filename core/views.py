from django.shortcuts import render
from listings.models import Listing

def home(request):

    latest_listings = Listing.objects.all().order_by('-created_at')[:6]

    return render(
        request,
        'core/index.html',
        {'latest_listings': latest_listings}
    )
