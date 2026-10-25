from django.test import TestCase
from django.urls import reverse

from core.models import ContactMessage
from listings.models import Listing
from users.models import User


class PublicTemplateRoutingTests(TestCase):

    def test_public_pages_render(self):
        page_names = (
            'home',
            'listings',
            'about',
            'contact',
            'privacy',
            'terms',
            'login',
            'register',
            'dashboard',
        )

        for page_name in page_names:
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                expected_status = 302 if page_name == 'dashboard' else 200
                self.assertEqual(response.status_code, expected_status)

    def test_shared_footer_renders_once_on_public_pages(self):
        page_names = (
            'home',
            'listings',
            'about',
            'contact',
            'privacy',
            'terms',
            'login',
            'register',
        )

        for page_name in page_names:
            with self.subTest(page=page_name):
                response = self.client.get(reverse(page_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'class="footer home-footer"')
                self.assertEqual(
                    response.content.count(b'class="footer home-footer"'),
                    1
                )

    def test_contact_form_fields_are_named_for_submission(self):
        response = self.client.get(reverse('contact'))

        self.assertContains(response, 'id="contactForm"')
        self.assertContains(response, 'name="fullName" required')
        self.assertContains(response, 'name="email" required')
        self.assertContains(response, 'name="subject" required')
        self.assertContains(response, 'name="message" rows="6" required')
        self.assertContains(response, 'src="/static/js/contact.js"')

    def test_valid_contact_submission_is_saved(self):
        response = self.client.post(
            reverse('contact'),
            {
                'fullName': 'Jane Doe',
                'email': 'jane@example.com',
                'phone': '+254700000000',
                'subject': 'general',
                'message': 'I need help with my account.',
                'priority': 'high',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        contact_message = ContactMessage.objects.get()
        self.assertEqual(contact_message.full_name, 'Jane Doe')
        self.assertEqual(contact_message.email, 'jane@example.com')
        self.assertEqual(contact_message.phone, '+254700000000')
        self.assertEqual(contact_message.subject, 'general')
        self.assertEqual(contact_message.priority, 'high')
        self.assertEqual(contact_message.status, 'new')
        self.assertContains(response, 'Thank you for contacting us!')

    def test_invalid_contact_submission_is_not_saved(self):
        response = self.client.post(
            reverse('contact'),
            {
                'fullName': '',
                'email': 'not-an-email',
                'subject': '',
                'message': '',
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 0)
        self.assertContains(response, 'Please enter your full name.')
        self.assertContains(response, 'Please enter a valid email address.')

    def test_homepage_links_to_django_listing_route(self):
        response = self.client.get(reverse('home'))

        self.assertContains(response, f'href="{reverse("listings")}"')
        self.assertContains(response, 'aria-controls="primary-navigation"')
        self.assertContains(response, 'id="primary-navigation"')
        self.assertContains(response, 'name="q"')
        self.assertContains(response, 'name="location"')
        self.assertContains(
            response,
            'href="https://www.facebook.com/share/1JqTA9Y4fj/"'
        )
        self.assertContains(response, 'aria-label="Visit AssetLinkAfrica on Facebook"')
        self.assertContains(response, 'mailto:assetlinkafrica254@gmail.com')

    def test_homepage_shows_live_listing_counts_and_latest_listing(self):
        owner = User.objects.create_user(
            username='home-listing-owner',
            password='test-password-123'
        )
        car = Listing.objects.create(
            owner=owner,
            title='Homepage SUV',
            description='A family vehicle for city and highway driving.',
            category='car',
            price='2300000.00',
            location='Nairobi',
            image='listings/home-car.jpg'
        )
        Listing.objects.create(
            owner=owner,
            title='Homepage land',
            description='A parcel ready for development.',
            category='land',
            price='5000000.00',
            location='Nakuru',
            image='listings/home-land.jpg'
        )

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, car.title)
        self.assertContains(response, 'name="q"')
        self.assertEqual(response.context['listing_count'], 2)
        self.assertEqual(response.context['car_count'], 1)
        self.assertEqual(response.context['land_count'], 1)
        self.assertEqual(response.context['location_count'], 2)
