from django.test import TestCase
from django.urls import reverse

from .models import Booking
from listings.models import Listing
from users.models import User


class BookingTemplateRoutingTests(TestCase):

    def test_bookings_page_requires_login(self):
        response = self.client.get(reverse('bookings'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('bookings')}"
        )

    def test_signed_in_user_can_view_bookings(self):
        user = User.objects.create_user(
            username='booking-user',
            password='test-password-123'
        )
        self.client.force_login(user)

        response = self.client.get(reverse('bookings'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/bookings.html')
        self.assertContains(response, 'No bookings yet')

    def test_booking_page_renders_listing_status_and_checkout_link(self):
        owner = User.objects.create_user(
            username='booking-listing-owner',
            password='test-password-123'
        )
        customer = User.objects.create_user(
            username='booking-customer',
            password='test-password-123'
        )
        listing = Listing.objects.create(
            owner=owner,
            title='Booking page test car',
            description='A test listing for the booking page.',
            category='car',
            price='1450000.00',
            location='Nairobi',
            image='listings/booking-test.jpg'
        )
        booking = Booking.objects.create(
            user=customer,
            listing=listing
        )
        self.client.force_login(customer)

        response = self.client.get(reverse('bookings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, listing.title)
        self.assertContains(response, 'Pending')
        self.assertContains(
            response,
            reverse('checkout', args=[booking.id])
        )

    def test_booking_creation_leads_to_checkout(self):
        owner = User.objects.create_user(
            username='listing-owner',
            password='test-password-123'
        )
        customer = User.objects.create_user(
            username='listing-customer',
            password='test-password-123'
        )
        listing = Listing.objects.create(
            owner=owner,
            title='Test car',
            description='A test listing',
            category='car',
            price='1200.00',
            location='Nairobi',
            image='listings/test.jpg'
        )
        self.client.force_login(customer)

        response = self.client.post(
            reverse('create_booking', args=[listing.id])
        )
        booking = Booking.objects.get(
            user=customer,
            listing=listing
        )

        self.assertRedirects(
            response,
            reverse('checkout', args=[booking.id])
        )
        listing.refresh_from_db()
        self.assertEqual(listing.status, 'booked')

    def test_rebooking_same_asset_reuses_existing_booking(self):
        owner = User.objects.create_user(
            username='repeat-booking-owner',
            password='test-password-123'
        )
        customer = User.objects.create_user(
            username='repeat-booking-customer',
            password='test-password-123'
        )
        listing = Listing.objects.create(
            owner=owner,
            title='Repeat booking test car',
            description='A test listing.',
            category='car',
            price='1200.00',
            location='Nairobi',
            image='listings/repeat-test.jpg'
        )
        self.client.force_login(customer)
        url = reverse('create_booking', args=[listing.id])

        first_response = self.client.post(url)
        booking = Booking.objects.get(user=customer, listing=listing)
        second_response = self.client.post(url)

        self.assertRedirects(first_response, reverse('checkout', args=[booking.id]))
        self.assertRedirects(second_response, reverse('checkout', args=[booking.id]))
        self.assertEqual(Booking.objects.filter(listing=listing).count(), 1)

    def test_another_customer_cannot_book_reserved_asset(self):
        owner = User.objects.create_user(
            username='reserved-listing-owner',
            password='test-password-123'
        )
        first_customer = User.objects.create_user(
            username='first-listing-customer',
            password='test-password-123'
        )
        second_customer = User.objects.create_user(
            username='second-listing-customer',
            password='test-password-123'
        )
        listing = Listing.objects.create(
            owner=owner,
            title='Reserved test car',
            description='A test listing.',
            category='car',
            price='1200.00',
            location='Nairobi',
            image='listings/reserved-test.jpg'
        )
        self.client.force_login(first_customer)
        self.client.post(reverse('create_booking', args=[listing.id]))
        self.client.force_login(second_customer)

        response = self.client.post(reverse('create_booking', args=[listing.id]))

        self.assertRedirects(response, reverse('details', args=[listing.id]))
        self.assertEqual(Booking.objects.filter(listing=listing).count(), 1)
