from django import forms
from django.utils import timezone

from .models import Listing


MAX_GALLERY_IMAGES = 8


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.ImageField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []

        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > MAX_GALLERY_IMAGES:
            raise forms.ValidationError(
                f'Upload no more than {MAX_GALLERY_IMAGES} additional images.'
            )
        return [forms.ImageField.clean(self, upload, initial) for upload in files]


class ListingForm(forms.ModelForm):
    listing_type = forms.ChoiceField(
        required=False,
        choices=Listing.LISTING_TYPE_CHOICES,
        initial='sale',
    )
    currency = forms.CharField(
        required=False,
        max_length=3,
        initial='KES',
    )
    vehicle_mileage_unit = forms.ChoiceField(
        required=False,
        choices=Listing.MILEAGE_UNIT_CHOICES,
        initial='km',
    )
    location_precision = forms.ChoiceField(
        required=False,
        choices=Listing.LOCATION_PRECISION_CHOICES,
        initial='exact',
    )
    gallery_images = MultipleImageField(
        required=False,
        label='Additional photos (optional)',
        help_text=f'Upload up to {MAX_GALLERY_IMAGES} extra photos. You can select multiple files.',
    )
    vehicle_features = forms.MultipleChoiceField(
        required=False,
        choices=Listing.VEHICLE_FEATURE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    land_utilities = forms.MultipleChoiceField(
        required=False,
        choices=Listing.UTILITIES_CHOICES,
        widget=forms.CheckboxSelectMultiple,
    )
    media_links = forms.CharField(
        required=False,
        label='360-degree, video, or survey links',
        help_text='Enter one publicly accessible media URL per line.',
        widget=forms.Textarea(attrs={'rows': 3}),
    )
    land_area = forms.DecimalField(
        required=False,
        min_value=0.01,
        max_digits=12,
        decimal_places=2,
    )


    class Meta:
        model = Listing
        fields = [
            'title',
            'description',
            'category',
            'listing_type',
            'price',
            'currency',
            'location',
            'image',
            'condition',
            'vehicle_make',
            'vehicle_model',
            'vehicle_trim',
            'vehicle_year',
            'vehicle_mileage',
            'vehicle_mileage_unit',
            'vehicle_engine_cc',
            'vehicle_fuel_type',
            'vehicle_transmission',
            'vehicle_drive_type',
            'vehicle_features',
            'land_dimensions',
            'land_area',
            'land_area_unit',
            'land_tenure',
            'land_zoning',
            'land_topography',
            'land_utilities',
            'land_proximity',
            'lease_price',
            'lease_period',
            'minimum_lease_months',
            'deposit_required',
            'bank_finance_allowed',
            'hire_purchase_deposit',
            'max_repayment_months',
            'latitude',
            'longitude',
            'location_precision',
            'media_links',
            'contact_name',
            'contact_phone',
            'contact_email',
            'gallery_images',
        ]
        labels = {
            'image': 'Main photo',
            'vehicle_make': 'Vehicle make',
            'vehicle_model': 'Vehicle model',
            'vehicle_trim': 'Trim / variant',
            'vehicle_year': 'Year',
            'vehicle_mileage': 'Odometer reading',
            'vehicle_mileage_unit': 'Mileage unit',
            'vehicle_engine_cc': 'Engine size (cc)',
            'land_area': 'Land size',
            'land_dimensions': 'Standard dimensions',
            'land_area_unit': 'Land size unit',
            'land_tenure': 'Ownership / title type',
            'land_zoning': 'Zoning / use',
            'land_topography': 'Topography / soil',
            'land_proximity': 'Proximity to roads, schools, malls, or towns',
            'listing_type': 'Listing type',
            'price': 'Base price',
            'lease_price': 'Lease / rental price',
            'minimum_lease_months': 'Minimum lease duration (months)',
            'deposit_required': 'Deposit required',
            'bank_finance_allowed': 'Bank finance allowed',
            'hire_purchase_deposit': 'Hire-purchase deposit',
            'max_repayment_months': 'Maximum repayment period (months)',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'location_precision': 'Map location visibility',
        }
        help_texts = {
            'image': 'Choose the main photo shown first on your listing.',
            'condition': 'Select the condition that best describes the asset.',
            'land_area': 'Enter the approximate land size.',
            'land_dimensions': 'For example, 50x100. Use the size unit field for the measurement unit.',
            'contact_phone': 'Use an international format where possible, e.g. +254712345678.',
            'contact_email': 'Shown to interested customers as a contact option.',
            'location_precision': 'For land, map coordinates are rounded to about 1 km when approximate is selected, or hidden when private is selected. The written location remains visible.',
            'latitude': 'Use decimal degrees; both coordinates are required together.',
            'longitude': 'Use decimal degrees; both coordinates are required together.',
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'e.g. Toyota Land Cruiser Prado 2020'}),
            'description': forms.Textarea(attrs={
                'placeholder': 'Describe the asset, its features, condition, access, and anything a buyer or renter should know.',
            }),
            'location': forms.TextInput(attrs={'placeholder': 'Area, town/city, county'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
            'condition': forms.Select(),
            'vehicle_make': forms.TextInput(attrs={'placeholder': 'e.g. Toyota'}),
            'vehicle_model': forms.TextInput(attrs={'placeholder': 'e.g. Land Cruiser Prado'}),
            'vehicle_trim': forms.TextInput(attrs={'placeholder': 'e.g. TX-L'}),
            'vehicle_year': forms.NumberInput(attrs={'placeholder': 'e.g. 2020', 'min': '1886'}),
            'vehicle_mileage': forms.NumberInput(attrs={'placeholder': 'e.g. 45000', 'min': '0'}),
            'vehicle_mileage_unit': forms.Select(),
            'vehicle_engine_cc': forms.NumberInput(attrs={'placeholder': 'e.g. 2000', 'min': '1'}),
            'land_dimensions': forms.TextInput(attrs={'placeholder': 'e.g. 50x100'}),
            'land_area': forms.NumberInput(attrs={'placeholder': 'e.g. 0.5', 'min': '0.01', 'step': '0.01'}),
            'land_area_unit': forms.Select(),
            'land_tenure': forms.Select(),
            'land_proximity': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g. 2 km from tarmac road; 1 km from schools',
            }),
            'price': forms.NumberInput(attrs={'placeholder': 'e.g. 2500000', 'min': '0', 'step': '0.01'}),
            'lease_price': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'deposit_required': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'hire_purchase_deposit': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'minimum_lease_months': forms.NumberInput(attrs={'min': '1'}),
            'max_repayment_months': forms.NumberInput(attrs={'min': '1'}),
            'latitude': forms.NumberInput(attrs={'min': '-90', 'max': '90', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'min': '-180', 'max': '180', 'step': '0.000001'}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'Contact person'}),
            'contact_phone': forms.TextInput(attrs={
                'type': 'tel',
                'placeholder': '+254712345678',
            }),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'contact@example.com'}),
        }

    def clean_vehicle_year(self):
        year = self.cleaned_data.get('vehicle_year')
        if year is not None and not 1886 <= year <= timezone.now().year + 1:
            raise forms.ValidationError('Enter a valid vehicle year.')
        return year

    def clean_media_links(self):
        links = self.cleaned_data.get('media_links', '')
        urls = [line.strip() for line in links.splitlines() if line.strip()]
        url_field = forms.URLField()
        cleaned_urls = []
        for url in urls:
            try:
                cleaned_urls.append(url_field.clean(url))
            except forms.ValidationError as exc:
                raise forms.ValidationError(
                    f'Enter a valid URL for media link "{url}".'
                ) from exc
        return cleaned_urls

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        latitude = cleaned_data.get('latitude')
        longitude = cleaned_data.get('longitude')
        if (latitude is None) != (longitude is None):
            self.add_error('latitude', 'Enter both latitude and longitude.')
            self.add_error('longitude', 'Enter both latitude and longitude.')
        if latitude is not None and not -90 <= latitude <= 90:
            self.add_error('latitude', 'Latitude must be between -90 and 90.')
        if longitude is not None and not -180 <= longitude <= 180:
            self.add_error('longitude', 'Longitude must be between -180 and 180.')

        currency = cleaned_data.get('currency')
        cleaned_data['currency'] = (currency or 'KES').upper()
        cleaned_data['listing_type'] = cleaned_data.get('listing_type') or 'sale'
        cleaned_data['vehicle_mileage_unit'] = (
            cleaned_data.get('vehicle_mileage_unit') or 'km'
        )
        cleaned_data['location_precision'] = (
            cleaned_data.get('location_precision')
            or ('approximate' if category == 'land' else 'exact')
        )

        if category == 'car':
            for field_name in (
                'vehicle_make',
                'vehicle_model',
                'vehicle_year',
                'condition',
            ):
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, 'This field is required for a car listing.')
            cleaned_data['land_area'] = None
            cleaned_data['land_area_unit'] = ''
            cleaned_data['land_tenure'] = ''
            cleaned_data['land_dimensions'] = ''
            cleaned_data['land_zoning'] = ''
            cleaned_data['land_topography'] = ''
            cleaned_data['land_utilities'] = []
            cleaned_data['land_proximity'] = ''
        elif category == 'land':
            if not cleaned_data.get('land_area') and not cleaned_data.get('land_dimensions'):
                self.add_error(
                    'land_dimensions',
                    'Enter standard dimensions or a total land area.',
                )
            if cleaned_data.get('land_area') and not cleaned_data.get('land_area_unit'):
                self.add_error('land_area_unit', 'Select the land area unit.')
            if not cleaned_data.get('land_tenure'):
                self.add_error('land_tenure', 'Select the title type.')
            cleaned_data['vehicle_make'] = ''
            cleaned_data['vehicle_model'] = ''
            cleaned_data['vehicle_year'] = None
            cleaned_data['vehicle_mileage'] = None
            cleaned_data['vehicle_trim'] = ''
            cleaned_data['vehicle_engine_cc'] = None
            cleaned_data['vehicle_fuel_type'] = ''
            cleaned_data['vehicle_transmission'] = ''
            cleaned_data['vehicle_drive_type'] = ''
            cleaned_data['vehicle_features'] = []

        if cleaned_data.get('listing_type') == 'lease':
            if not cleaned_data.get('lease_price'):
                self.add_error('lease_price', 'Enter the recurring lease or rental price.')
            if not cleaned_data.get('lease_period'):
                self.add_error('lease_period', 'Select whether the price is per month or year.')

        if cleaned_data.get('listing_type') == 'hire_purchase':
            if not cleaned_data.get('hire_purchase_deposit'):
                self.add_error(
                    'hire_purchase_deposit',
                    'Enter the required hire-purchase deposit.',
                )
            if not cleaned_data.get('max_repayment_months'):
                self.add_error(
                    'max_repayment_months',
                    'Enter the maximum repayment period.',
                )

        return cleaned_data
