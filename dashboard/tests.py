from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from bookings.models import Booking
from listings.models import Listing, Subscription, SubscriptionPlan
from users.models import User


class DashboardPageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='dashboard-user',
            password='test-password-123'
        )
        self.listing = Listing.objects.create(
            owner=self.user,
            title='Dashboard test car',
            description='A dashboard test listing',
            category='car',
            price='1800000.00',
            location='Nairobi',
            image='listings/dashboard-test.jpg'
        )
        self.booking = Booking.objects.create(
            user=self.user,
            listing=self.listing
        )

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}"
        )

    def test_dashboard_renders_user_data_and_template_links(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/dashboard.html')
        self.assertContains(response, self.listing.title)
        self.assertContains(response, reverse('details', args=[self.listing.id]))
        self.assertContains(response, reverse('bookings'))
        self.assertContains(response, reverse('create_listing'))
        self.assertContains(response, 'Recent bookings')
        self.assertContains(response, 'Listing subscription')
        self.assertContains(response, 'Basic')
        self.assertContains(response, '1 of 1')
        self.assertContains(response, reverse('subscription_plans'))

    def test_dashboard_shows_active_paid_plan_details(self):
        premium_plan = SubscriptionPlan.objects.get(code='premium')
        subscription = Subscription.objects.create(
            user=self.user,
            plan=premium_plan,
            ends_at=timezone.now() + timedelta(days=30),
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Premium')
        self.assertContains(response, '1 of 5')
        self.assertContains(response, 'KES 3499/month')
        self.assertContains(
            response,
            subscription.ends_at.strftime('%b %-d, %Y'),
        )
