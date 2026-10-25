from django.contrib import messages
from django.shortcuts import render

from listings.models import Listing

from .forms import ContactForm
from .models import ContactMessage


def home(request):

    latest_listings = Listing.objects.all().order_by('-created_at')[:6]
    listings = Listing.objects.all()

    return render(
        request,
        'core/index.html',
        {
            'latest_listings': latest_listings,
            'listing_count': listings.count(),
            'car_count': listings.filter(category='car').count(),
            'land_count': listings.filter(category='land').count(),
            'location_count': listings.values('location').distinct().count(),
        }
    )


def about(request):
    return render(request, 'core/pages/about.html')


def contact(request):
    form = ContactForm(request.POST or None)

    if request.method == 'POST':
        if form.is_valid():
            ContactMessage.objects.create(
                full_name=form.cleaned_data['fullName'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message'],
                priority=form.cleaned_data['priority'] or 'medium',
            )
            messages.success(
                request,
                'Thank you for contacting us! We will respond within 24 hours.'
            )
            return render(
                request,
                'core/pages/contact.html',
                {'form': ContactForm(), 'form_success': 'Thank you for contacting us! We will respond within 24 hours.'}
            )

        return render(request, 'core/pages/contact.html', {'form': form})

    return render(request, 'core/pages/contact.html', {'form': form})


def privacy(request):
    return render(request, 'core/pages/privacy.html')


def terms(request):
    return render(request, 'core/pages/terms.html')
