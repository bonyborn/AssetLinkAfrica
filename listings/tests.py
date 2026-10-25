from io import BytesIO
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from .models import Listing, Subscription, SubscriptionPlan
from users.models import User


class ListingPageTests(TestCase):

    @staticmethod
    def uploaded_image(filename):
        image_data = BytesIO()
        Image.new('RGB', (1, 1)).save(image_data, format='PNG')
        return SimpleUploadedFile(
            filename,
            image_data.getvalue(),
            content_type='image/png',
        )

    def setUp(self):
        self.owner = User.objects.create_user(
            username='listing-owner',
            password='test-password-123'
        )
        self.listing = Listing.objects.create(
            owner=self.owner,
            title='Nairobi family SUV',
            description='A well-maintained vehicle ready for your next trip.',
            category='car',
            price='2500000.00',
            location='Nairobi, Kenya',
            image='listings/test.jpg'
        )

    def test_listing_card_renders_with_live_listing_details(self):
        response = self.client.get(reverse('listings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.listing.title)
        self.assertContains(response, self.listing.location)
        self.assertContains(response, reverse('details', args=[self.listing.id]))
        self.assertContains(response, 'Search listings')

    def test_listing_filters_can_be_cleared_when_no_results_match(self):
        response = self.client.get(
            reverse('listings'),
            {'q': 'unmatched asset'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No matching listings')
        self.assertContains(response, 'Clear filters')
        self.assertNotContains(response, self.listing.title)

    def test_listing_search_keeps_query_visible_in_the_search_field(self):
        response = self.client.get(
            reverse('listings'),
            {'q': 'Nairobi family'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Nairobi family"')
        self.assertContains(response, 'placeholder="Try a Toyota or a plot"')

    def test_listing_detail_uses_styled_detail_template(self):
        response = self.client.get(
            reverse('details', args=[self.listing.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'listing-detail-card')
        self.assertContains(response, 'Log in to book')

    def test_listing_detail_displays_available_asset_and_contact_details(self):
        self.listing.vehicle_make = 'Toyota'
        self.listing.vehicle_model = 'Prado'
        self.listing.vehicle_year = 2020
        self.listing.vehicle_mileage = 45000
        self.listing.condition = 'good'
        self.listing.contact_name = 'Listing contact'
        self.listing.contact_phone = '+254712345678'
        self.listing.contact_email = 'contact@example.com'
        self.listing.save()

        response = self.client.get(reverse('details', args=[self.listing.id]))

        self.assertContains(response, 'Vehicle details')
        self.assertContains(response, 'Toyota')
        self.assertContains(response, 'Prado')
        self.assertContains(response, '45000 km')
        self.assertContains(response, 'Listing contact')
        self.assertContains(response, 'mailto:contact@example.com')

    def test_create_listing_accepts_optional_gallery_images_and_detail_fields(self):
        owner = User.objects.create_user(
            username='gallery-owner',
            password='test-password-123',
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Gallery listing',
                'description': 'Clear details and multiple photos.',
                'category': 'car',
                'price': '1000.00',
                'location': 'Nairobi',
                'image': self.uploaded_image('cover.png'),
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Corolla',
                'vehicle_year': '2021',
                'vehicle_mileage': '30000',
                'condition': 'excellent',
                'contact_name': 'Contact person',
                'contact_phone': '+254712345678',
                'contact_email': 'contact@example.com',
                'gallery_images': [
                    self.uploaded_image('side.png'),
                    self.uploaded_image('interior.png'),
                ],
            },
        )

        listing = Listing.objects.get(title='Gallery listing')
        self.assertRedirects(response, reverse('listings'))
        self.assertEqual(listing.vehicle_make, 'Toyota')
        self.assertEqual(listing.vehicle_year, 2021)
        self.assertEqual(listing.contact_phone, '+254712345678')
        self.assertEqual(listing.images.count(), 2)
        detail_response = self.client.get(reverse('details', args=[listing.id]))
        self.assertContains(detail_response, 'View additional photo 1')

    def test_create_car_listing_saves_searchable_specs_terms_and_media(self):
        owner = User.objects.create_user(
            username='blueprint-car-owner',
            password='test-password-123',
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Verified-spec SUV',
                'description': 'Detailed car listing.',
                'category': 'car',
                'listing_type': 'hire_purchase',
                'price': '2500000',
                'currency': 'kes',
                'location': 'Nairobi',
                'image': self.uploaded_image('blueprint-car.png'),
                'condition': 'foreign_used',
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Land Cruiser',
                'vehicle_trim': 'VX',
                'vehicle_year': '2022',
                'vehicle_mileage': '45000',
                'vehicle_mileage_unit': 'km',
                'vehicle_engine_cc': '2800',
                'vehicle_fuel_type': 'diesel',
                'vehicle_transmission': 'automatic',
                'vehicle_drive_type': '4wd',
                'vehicle_features': ['sunroof', 'reverse_camera'],
                'hire_purchase_deposit': '500000',
                'max_repayment_months': '36',
                'latitude': '-1.286389',
                'longitude': '36.817223',
                'media_links': 'https://media.example.com/interior-360',
            },
        )

        listing = Listing.objects.get(title='Verified-spec SUV')
        self.assertRedirects(response, reverse('listings'))
        self.assertEqual(len(listing.public_id), 32)
        self.assertEqual(listing.currency, 'KES')
        self.assertEqual(listing.verification_status, 'unverified')
        self.assertEqual(listing.vehicle_trim, 'VX')
        self.assertEqual(listing.vehicle_features, ['sunroof', 'reverse_camera'])
        self.assertEqual(listing.hire_purchase_deposit, Decimal('500000'))
        self.assertEqual(listing.media_links, ['https://media.example.com/interior-360'])
        self.assertIsNotNone(listing.expires_at)

        detail_response = self.client.get(reverse('details', args=[listing.id]))
        self.assertContains(detail_response, 'Hire-purchase deposit')
        self.assertContains(detail_response, 'Reverse camera')
        self.assertContains(detail_response, 'View media 1')

    def test_create_land_listing_accepts_standard_dimensions_and_hides_private_coordinates(self):
        owner = User.objects.create_user(
            username='blueprint-land-owner',
            password='test-password-123',
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Residential plot',
                'description': 'A plot measured by standard dimensions.',
                'category': 'land',
                'listing_type': 'sale',
                'price': '1500000',
                'location': 'Kiambu',
                'image': self.uploaded_image('blueprint-land.png'),
                'land_dimensions': '50x100',
                'land_tenure': 'freehold',
                'land_zoning': 'residential',
                'land_topography': 'red_soil',
                'land_utilities': ['mains_water', 'electricity'],
                'land_proximity': '1 km from the tarmac road',
                'latitude': '-1.171',
                'longitude': '36.835',
                'location_precision': 'private',
            },
        )

        listing = Listing.objects.get(title='Residential plot')
        self.assertRedirects(response, reverse('listings'))
        self.assertEqual(listing.land_dimensions, '50x100')
        self.assertIsNone(listing.land_area)
        self.assertEqual(listing.land_utilities, ['mains_water', 'electricity'])

        detail_response = self.client.get(reverse('details', args=[listing.id]))
        self.assertContains(detail_response, '50x100')
        self.assertContains(detail_response, 'Mains water')
        self.assertNotContains(detail_response, '-1.171, 36.835')

    def test_land_coordinates_default_to_approximate_public_display(self):
        owner = User.objects.create_user(
            username='approximate-land-owner',
            password='test-password-123',
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Approximate map land listing',
                'description': 'Map location should be approximate by default.',
                'category': 'land',
                'price': '1500000',
                'location': 'Kiambu',
                'image': self.uploaded_image('approximate-land.png'),
                'land_dimensions': '50x100',
                'land_tenure': 'freehold',
                'latitude': '-1.171234',
                'longitude': '36.835678',
            },
        )

        listing = Listing.objects.get(title='Approximate map land listing')
        self.assertRedirects(response, reverse('listings'))
        self.assertEqual(listing.location_precision, 'approximate')

        detail_response = self.client.get(reverse('details', args=[listing.id]))
        self.assertContains(detail_response, 'Approx. -1.17, 36.84')
        self.assertNotContains(detail_response, '-1.171234')

    def test_create_listing_form_prefills_optional_contact_details(self):
        owner = User.objects.create_user(
            username='prefill-owner',
            password='test-password-123',
            first_name='Asset',
            last_name='Owner',
            email='owner@example.com',
            phone_number='+254712345678',
        )
        self.client.force_login(owner)

        response = self.client.get(reverse('create_listing'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="Asset Owner"')
        self.assertContains(response, 'value="+254712345678"')
        self.assertContains(response, 'value="owner@example.com"')
        self.assertContains(response, 'multiple')

    def test_free_plan_allows_one_persisted_listing_only(self):
        basic_plan = SubscriptionPlan.objects.get(code='basic')
        owner = User.objects.create_user(
            username='basic-plan-owner',
            password='test-password-123'
        )
        self.client.force_login(owner)

        response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'First persisted listing',
                'description': 'An asset on the basic plan.',
                'category': 'car',
                'price': '1000.00',
                'location': 'Nairobi',
                'image': self.uploaded_image('asset.png'),
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Corolla',
                'vehicle_year': '2020',
                'condition': 'good',
            },
        )

        listing = Listing.objects.get(owner=owner)
        self.assertRedirects(response, reverse('listings'))
        self.assertEqual(listing.title, 'First persisted listing')
        self.assertEqual(listing.owner_id, owner.id)
        self.assertEqual(basic_plan.maximum_listings, 1)

        rejected_response = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Second listing is not allowed',
                'description': 'This exceeds the basic plan.',
                'category': 'land',
                'price': '2000.00',
                'location': 'Nairobi',
                'image': self.uploaded_image('second.png'),
                'land_area': '0.5',
                'land_area_unit': 'acres',
                'land_tenure': 'freehold',
            },
        )

        self.assertEqual(rejected_response.status_code, 200)
        self.assertContains(rejected_response, 'Basic plan allows up to 1 listing')
        self.assertEqual(Listing.objects.filter(owner=owner).count(), 1)

    def test_premium_subscription_persists_and_allows_five_listings(self):
        premium_plan = SubscriptionPlan.objects.get(code='premium')
        featured_plan = SubscriptionPlan.objects.get(code='featured')
        owner = User.objects.create_user(
            username='premium-plan-owner',
            password='test-password-123'
        )
        subscription = Subscription.objects.create(
            user=owner,
            plan=premium_plan,
        )
        for listing_number in range(4):
            Listing.objects.create(
                owner=owner,
                title=f'Existing premium listing {listing_number}',
                description='A persisted asset on a premium subscription.',
                category='car',
                price='1000.00',
                location='Nairobi',
                image='listings/premium-existing.jpg',
            )
        self.client.force_login(owner)

        fifth_listing = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Fifth premium listing',
                'description': 'The last listing allowed by Premium.',
                'category': 'car',
                'price': '1000.00',
                'location': 'Nairobi',
                'image': self.uploaded_image('fifth.png'),
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Corolla',
                'vehicle_year': '2020',
                'condition': 'good',
            },
        )
        sixth_listing = self.client.post(
            reverse('create_listing'),
            {
                'title': 'Sixth premium listing',
                'description': 'This exceeds the Premium limit.',
                'category': 'car',
                'price': '1000.00',
                'location': 'Nairobi',
                'image': self.uploaded_image('sixth.png'),
                'vehicle_make': 'Toyota',
                'vehicle_model': 'Corolla',
                'vehicle_year': '2020',
                'condition': 'good',
            },
        )

        self.assertEqual(subscription.plan.monthly_price, Decimal('3499.00'))
        self.assertEqual(premium_plan.minimum_listings, 2)
        self.assertEqual(premium_plan.maximum_listings, 5)
        self.assertEqual(Subscription.active_for_user(owner), subscription)
        self.assertEqual(featured_plan.minimum_listings, 6)
        self.assertIsNone(featured_plan.maximum_listings)
        self.assertEqual(featured_plan.monthly_price, Decimal('4999.00'))
        self.assertRedirects(fifth_listing, reverse('listings'))
        self.assertEqual(
            Listing.objects.filter(owner=owner).count(),
            premium_plan.maximum_listings,
        )
        self.assertEqual(sixth_listing.status_code, 200)
        self.assertContains(sixth_listing, 'Premium plan allows up to 5 listing')
        self.assertFalse(
            Listing.objects.filter(owner=owner, title='Sixth premium listing').exists()
        )
