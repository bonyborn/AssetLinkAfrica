import uuid
from datetime import timedelta

from django.db import models
from django.conf import settings
from django.db.models import Q
from django.utils import timezone


def default_listing_expiry():
    return timezone.now() + timedelta(days=30)


def generate_public_listing_id():
    return uuid.uuid4().hex


class Listing(models.Model):

    CATEGORY_CHOICES = (
        ('car', 'Car'),
        ('land', 'Land'),
    )

    LISTING_TYPE_CHOICES = (
        ('sale', 'Sale'),
        ('lease', 'Lease'),
        ('hire_purchase', 'Hire-purchase'),
    )

    VERIFICATION_STATUS_CHOICES = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending'),
        ('verified', 'Verified'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('booked', 'Booked'),
    )

    CONDITION_CHOICES = (
        ('new', 'New'),
        ('foreign_used', 'Foreign used (import)'),
        ('locally_used', 'Locally used'),
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('needs_work', 'Needs work'),
    )

    MILEAGE_UNIT_CHOICES = (
        ('km', 'Kilometres'),
        ('miles', 'Miles'),
    )

    LAND_AREA_UNIT_CHOICES = (
        ('acres', 'Acres'),
        ('hectares', 'Hectares'),
        ('sqm', 'Square metres'),
        ('sqft', 'Square feet'),
    )

    LAND_TENURE_CHOICES = (
        ('freehold', 'Freehold'),
        ('leasehold', 'Leasehold'),
        ('sectional_title', 'Sectional title'),
        ('share_certificate', 'Share certificate'),
        ('other', 'Other / not specified'),
    )

    LAND_ZONING_CHOICES = (
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('agricultural', 'Agricultural'),
        ('mixed_use', 'Mixed-use'),
    )

    LAND_TOPOGRAPHY_CHOICES = (
        ('flat', 'Flat'),
        ('sloping', 'Sloping'),
        ('rocky', 'Rocky'),
        ('red_soil', 'Red soil'),
        ('black_cotton_soil', 'Black cotton soil'),
    )

    FUEL_TYPE_CHOICES = (
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('other', 'Other'),
    )

    TRANSMISSION_CHOICES = (
        ('automatic', 'Automatic'),
        ('manual', 'Manual'),
    )

    DRIVE_TYPE_CHOICES = (
        ('awd', 'AWD'),
        ('4wd', '4WD'),
        ('fwd', 'FWD'),
        ('rwd', 'RWD'),
    )

    LEASE_PERIOD_CHOICES = (
        ('month', 'Per month'),
        ('year', 'Per year'),
    )

    LOCATION_PRECISION_CHOICES = (
        ('exact', 'Exact location'),
        ('approximate', 'Approximate location'),
        ('private', 'Do not show map location'),
    )

    UTILITIES_CHOICES = (
        ('mains_water', 'Mains water'),
        ('electricity', 'Electricity on-site'),
        ('borehole', 'Borehole'),
        ('sewer', 'Sewer line connection'),
        ('paved_road', 'Paved access road'),
    )

    VEHICLE_FEATURE_CHOICES = (
        ('sunroof', 'Sunroof'),
        ('leather_seats', 'Leather seats'),
        ('reverse_camera', 'Reverse camera'),
        ('cruise_control', 'Cruise control'),
        ('android_auto', 'Android Auto'),
        ('apple_carplay', 'Apple CarPlay'),
        ('third_row', 'Third-row seating'),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='listings'
    )

    public_id = models.CharField(
        max_length=32,
        default=generate_public_listing_id,
        unique=True,
        editable=False,
    )
    title = models.CharField(max_length=255)

    description = models.TextField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    currency = models.CharField(max_length=3, default='KES')
    listing_type = models.CharField(
        max_length=20,
        choices=LISTING_TYPE_CHOICES,
        default='sale',
        db_index=True,
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified',
        db_index=True,
    )
    expires_at = models.DateTimeField(default=default_listing_expiry, db_index=True)

    location = models.CharField(
        max_length=255
    )

    image = models.ImageField(
        upload_to='listings/'
    )

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        blank=True,
    )
    vehicle_make = models.CharField(max_length=100, blank=True)
    vehicle_model = models.CharField(max_length=100, blank=True)
    vehicle_trim = models.CharField(max_length=100, blank=True)
    vehicle_year = models.PositiveSmallIntegerField(null=True, blank=True)
    vehicle_mileage = models.PositiveIntegerField(null=True, blank=True)
    vehicle_mileage_unit = models.CharField(
        max_length=10,
        choices=MILEAGE_UNIT_CHOICES,
        default='km',
    )
    vehicle_engine_cc = models.PositiveIntegerField(null=True, blank=True)
    vehicle_fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_TYPE_CHOICES,
        blank=True,
    )
    vehicle_transmission = models.CharField(
        max_length=20,
        choices=TRANSMISSION_CHOICES,
        blank=True,
    )
    vehicle_drive_type = models.CharField(
        max_length=10,
        choices=DRIVE_TYPE_CHOICES,
        blank=True,
    )
    vehicle_features = models.JSONField(default=list, blank=True)
    land_dimensions = models.CharField(max_length=100, blank=True)
    land_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    land_area_unit = models.CharField(
        max_length=20,
        choices=LAND_AREA_UNIT_CHOICES,
        blank=True,
    )
    land_tenure = models.CharField(
        max_length=20,
        choices=LAND_TENURE_CHOICES,
        blank=True,
    )
    land_zoning = models.CharField(
        max_length=20,
        choices=LAND_ZONING_CHOICES,
        blank=True,
    )
    land_topography = models.CharField(
        max_length=30,
        choices=LAND_TOPOGRAPHY_CHOICES,
        blank=True,
    )
    land_utilities = models.JSONField(default=list, blank=True)
    land_proximity = models.TextField(blank=True)

    lease_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    lease_period = models.CharField(
        max_length=10,
        choices=LEASE_PERIOD_CHOICES,
        blank=True,
    )
    minimum_lease_months = models.PositiveSmallIntegerField(null=True, blank=True)
    deposit_required = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    bank_finance_allowed = models.BooleanField(default=False)
    hire_purchase_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_repayment_months = models.PositiveSmallIntegerField(null=True, blank=True)

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    location_precision = models.CharField(
        max_length=15,
        choices=LOCATION_PRECISION_CHOICES,
        default='exact',
    )
    media_links = models.JSONField(default=list, blank=True)

    contact_name = models.CharField(max_length=150, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=('category', 'listing_type', 'verification_status'),
                name='listing_search_filters_idx',
            ),
            models.Index(
                fields=('status', 'expires_at'),
                name='listing_status_expiry_idx',
            ),
            models.Index(
                fields=('vehicle_make', 'vehicle_model', 'vehicle_year'),
                name='listing_vehicle_search_idx',
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(latitude__isnull=True, longitude__isnull=True)
                    | Q(latitude__isnull=False, longitude__isnull=False)
                ),
                name='listing_coordinates_pair',
            ),
            models.CheckConstraint(
                condition=(
                    Q(latitude__isnull=True)
                    | Q(latitude__gte=-90, latitude__lte=90)
                ),
                name='listing_latitude_range',
            ),
            models.CheckConstraint(
                condition=(
                    Q(longitude__isnull=True)
                    | Q(longitude__gte=-180, longitude__lte=180)
                ),
                name='listing_longitude_range',
            ),
        ]

    def get_vehicle_features_display(self):
        labels = dict(self.VEHICLE_FEATURE_CHOICES)
        return [labels[value] for value in self.vehicle_features if value in labels]

    def get_land_utilities_display(self):
        labels = dict(self.UTILITIES_CHOICES)
        return [labels[value] for value in self.land_utilities if value in labels]

    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to='listings/gallery/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('uploaded_at', 'id')

    def __str__(self):
        return f'Image for {self.listing.title}'


class SubscriptionPlan(models.Model):

    CODE_CHOICES = (
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('featured', 'Featured'),
    )

    code = models.CharField(
        max_length=20,
        choices=CODE_CHOICES,
        unique=True
    )

    minimum_listings = models.PositiveIntegerField(default=1)

    maximum_listings = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    monthly_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('monthly_price', 'minimum_listings')
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(maximum_listings__isnull=True)
                    | Q(maximum_listings__gte=models.F('minimum_listings'))
                ),
                name='subscription_plan_valid_listing_range',
            ),
        ]

    def __str__(self):
        return self.get_code_display()


class Subscription(models.Model):

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    starts_at = models.DateTimeField(default=timezone.now)

    ends_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-starts_at', '-created_at')
        constraints = [
            models.UniqueConstraint(
                fields=('user',),
                condition=Q(status='active'),
                name='one_active_subscription_per_user',
            ),
            models.CheckConstraint(
                condition=Q(ends_at__isnull=True) | Q(ends_at__gt=models.F('starts_at')),
                name='subscription_end_after_start',
            ),
        ]

    @classmethod
    def active_for_user(cls, user, at=None):
        at = at or timezone.now()
        return (
            cls.objects.filter(
                user=user,
                status='active',
                starts_at__lte=at,
            )
            .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=at))
            .select_related('plan')
            .first()
        )

    def __str__(self):
        return f'{self.user} - {self.plan}'
