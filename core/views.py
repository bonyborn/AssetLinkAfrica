from django.shortcuts import render

from listings.models import Listing


def home(request):

    latest_listings = Listing.objects.all().order_by("-created_at")[:6]

    return render(request, "core/index.html", {"latest_listings": latest_listings})


def privacy(request):
    return render(request, "core/privacy.html")


def terms(request):
    return render(request, "core/terms.html")


def contact(request):
    return render(request, "core/contact.html")
