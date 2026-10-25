from django.db import models


class ContactMessage(models.Model):
    SUBJECT_CHOICES = (
        ('general', 'General Inquiry'),
        ('listing', 'Listing Support'),
        ('booking', 'Booking Issue'),
        ('payment', 'Payment Question'),
        ('account', 'Account Management'),
        ('partnership', 'Partnership Opportunity'),
        ('complaint', 'Complaint'),
    )
    PRIORITY_CHOICES = (
        ('low', 'Low - General question'),
        ('medium', 'Medium - Need assistance'),
        ('high', 'High - Urgent issue'),
    )
    STATUS_CHOICES = (
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('resolved', 'Resolved'),
    )

    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.full_name} — {self.get_subject_display()}'
