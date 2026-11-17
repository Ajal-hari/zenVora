
from django.db import models
from django.utils import timezone

from feedback.models import Student


# ============================================================
# LOST & FOUND ITEMS
# ============================================================

class LostItem(models.Model):

    CATEGORY_CHOICES = [
        ('Electronics', 'Electronics'),
        ('ID Card', 'ID Card'),
        ('Books', 'Books'),
        ('Accessories', 'Accessories'),
        ('Keys', 'Keys'),
        ('Wallet', 'Wallet'),
        ('Other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('returned', 'Returned'),
    ]

    name = models.CharField(
        max_length=150
    )

    description = models.TextField()

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Other'
    )

    found_location = models.CharField(
        max_length=200
    )

    found_date = models.DateField(
        default=timezone.localdate
    )

    image_url = models.URLField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='available',
        db_index=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


# ============================================================
# LOST ITEM BOOKINGS
# ============================================================

class LostItemBooking(models.Model):

    BOOKING_STATUS_CHOICES = [
        ('pending', 'Pending Verification'),
        ('collected', 'Collected'),
        ('cancelled', 'Cancelled'),
    ]

    item = models.ForeignKey(
        LostItem,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='lost_item_bookings'
    )

    collection_date = models.DateField()

    collection_time = models.TimeField()

    ownership_details = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=BOOKING_STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return "{} - {}".format(
            self.item.name,
            self.student.name
        )
