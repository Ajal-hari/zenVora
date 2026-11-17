
from datetime import datetime

from django.contrib import messages
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from feedback.models import Student
from .models import LostItem, LostItemBooking


# ============================================================
# LOGIN HELPERS
# ============================================================

def get_student(request):
    student_id = request.session.get('student_id')

    if not student_id:
        return None

    return Student.objects.filter(pk=student_id).first()


def is_admin(request):
    return request.user.is_authenticated and request.user.is_active and request.user.is_staff


def back_to_admin(request, edit_id=None):
    """
    Return to the unified admin dashboard after an
    action submitted from its Lost & Found section.
    """

    if request.POST.get('return_to') == 'unified':
        return redirect('/admin-dashboard/#lost-found')

    if edit_id is not None:
        return redirect('lost_found_edit', item_id=edit_id)

    return redirect('lost_found_admin')


# ============================================================
# ITEM FORM VALIDATION
# ============================================================

def validate_item_post(request):

    name = request.POST.get('name', '').strip()

    description = request.POST.get(
        'description', ''
    ).strip()

    category = request.POST.get(
        'category', 'Other'
    ).strip()

    location = request.POST.get(
        'found_location', ''
    ).strip()

    found_date_text = request.POST.get(
        'found_date', ''
    ).strip()

    image_url = request.POST.get(
        'image_url', ''
    ).strip()

    if not name or not description or not location:
        raise ValueError(
            'Complete all required item fields.'
        )

    if category not in dict(LostItem.CATEGORY_CHOICES):
        raise ValueError('Select a valid category.')

    try:
        found_date = datetime.strptime(
            found_date_text, '%Y-%m-%d'
        ).date()
    except ValueError:
        raise ValueError('Enter a valid found date.')

    if image_url:
        try:
            URLValidator(
                schemes=['http', 'https']
            )(image_url)
        except ValidationError:
            raise ValueError(
                'Enter a valid image URL or leave it blank.'
            )

    return {
        'name': name,
        'description': description,
        'category': category,
        'found_location': location,
        'found_date': found_date,
        'image_url': image_url,
    }


# ============================================================
# STUDENT - VIEW AVAILABLE ITEMS
# ============================================================

def item_list(request):

    student = get_student(request)

    if not student:
        messages.error(
            request,
            'Please log in as a student.'
        )
        return redirect('/login/')

    items = LostItem.objects.filter(
        status='available'
    ).order_by('-created_at')

    my_bookings = LostItemBooking.objects.filter(
        student=student
    ).select_related('item').order_by('-created_at')

    return render(
        request,
        'lost_found/item_list.html',
        {
            'student': student,
            'items': items,
            'my_bookings': my_bookings,
        }
    )


# ============================================================
# STUDENT - BOOK AN ITEM
# ============================================================

def book_item(request, item_id):

    student = get_student(request)

    if not student:
        messages.error(
            request,
            'Please log in as a student.'
        )
        return redirect('/login/')

    item = get_object_or_404(
        LostItem,
        pk=item_id
    )

    if item.status != 'available':
        messages.error(
            request,
            'This item is no longer available.'
        )
        return redirect('lost_found_list')

    if request.method == 'POST':

        date_text = request.POST.get(
            'collection_date', ''
        ).strip()

        time_text = request.POST.get(
            'collection_time', ''
        ).strip()

        ownership = request.POST.get(
            'ownership_details', ''
        ).strip()

        try:
            collection_date = datetime.strptime(
                date_text, '%Y-%m-%d'
            ).date()

            collection_time = datetime.strptime(
                time_text, '%H:%M'
            ).time()

        except ValueError:
            messages.error(
                request,
                'Enter a valid collection date and time.'
            )

            return redirect(
                'lost_found_book',
                item_id=item.pk
            )

        appointment = timezone.make_aware(
            datetime.combine(
                collection_date,
                collection_time
            ),
            timezone.get_current_timezone()
        )

        if appointment <= timezone.now():
            messages.error(
                request,
                'Please choose a future collection date and time.'
            )

            return redirect(
                'lost_found_book',
                item_id=item.pk
            )

        if len(ownership) < 10:
            messages.error(
                request,
                'Ownership details must be at least 10 characters.'
            )

            return redirect(
                'lost_found_book',
                item_id=item.pk
            )

        with transaction.atomic():

            updated = LostItem.objects.filter(
                pk=item.pk,
                status='available'
            ).update(
                status='reserved'
            )

            if not updated:
                messages.error(
                    request,
                    'Another student has reserved this item.'
                )
                return redirect('lost_found_list')

            LostItemBooking.objects.create(
                item=item,
                student=student,
                collection_date=collection_date,
                collection_time=collection_time,
                ownership_details=ownership,
                status='pending'
            )

        messages.success(
            request,
            'Item reserved! Visit admin for ownership verification.'
        )

        return redirect('lost_found_list')

    return render(
        request,
        'lost_found/book_item.html',
        {
            'student': student,
            'item': item,
            'today': timezone.localdate(),
        }
    )


# ============================================================
# ADMIN - EXISTING STANDALONE PAGE
# ============================================================

def admin_items(request):

    if not is_admin(request):
        return redirect('/admin-login/')

    return render(
        request,
        'lost_found/admin_items.html',
        {
            'items': LostItem.objects.all().order_by(
                '-created_at'
            ),

            'bookings': LostItemBooking.objects.select_related(
                'item', 'student'
            ).order_by('-created_at'),
        }
    )


# ============================================================
# ADMIN - ADD FOUND ITEM
# ============================================================

@require_POST
def admin_add_item(request):

    if not is_admin(request):
        return redirect('/admin-login/')

    try:
        data = validate_item_post(request)

    except ValueError as error:
        messages.error(request, str(error))
        return back_to_admin(request)

    LostItem.objects.create(
        status='available',
        **data
    )

    messages.success(
        request,
        'Found item added successfully.'
    )

    return back_to_admin(request)


# ============================================================
# ADMIN - EDIT ITEM
# ============================================================

def admin_edit_item(request, item_id):

    if not is_admin(request):
        return redirect('/admin-login/')

    item = get_object_or_404(
        LostItem,
        pk=item_id
    )

    if request.method == 'POST':

        try:
            data = validate_item_post(request)

        except ValueError as error:
            messages.error(request, str(error))

            return back_to_admin(
                request,
                edit_id=item.pk
            )

        for field, value in data.items():
            setattr(item, field, value)

        item.save()

        messages.success(
            request,
            'Item updated successfully.'
        )

        return back_to_admin(request)

    return render(
        request,
        'lost_found/edit_item.html',
        {
            'item': item,
            'categories': LostItem.CATEGORY_CHOICES,
        }
    )


# ============================================================
# ADMIN - DELETE ITEM
# ============================================================

@require_POST
def admin_delete_item(request, item_id):

    if not is_admin(request):
        return redirect('/admin-login/')

    with transaction.atomic():

        item = get_object_or_404(
            LostItem.objects.select_for_update(),
            pk=item_id
        )

        if item.status == 'reserved':
            messages.error(
                request,
                'Cancel the pending booking before deleting the item.'
            )

        else:
            item.delete()

            messages.success(
                request,
                'Item deleted successfully.'
            )

    return back_to_admin(request)


# ============================================================
# ADMIN - CONFIRM ITEM RETURN
# ============================================================

@require_POST
def admin_return_item(request, booking_id):

    if not is_admin(request):
        return redirect('/admin-login/')

    with transaction.atomic():

        booking = get_object_or_404(
            LostItemBooking.objects.select_for_update(),
            pk=booking_id
        )

        if booking.status != 'pending':
            messages.error(
                request,
                'Only pending bookings can be returned.'
            )

        else:

            updated = LostItem.objects.filter(
                pk=booking.item_id,
                status='reserved'
            ).update(
                status='returned'
            )

            if updated:

                booking.status = 'collected'

                booking.save(
                    update_fields=[
                        'status',
                        'updated_at'
                    ]
                )

                messages.success(
                    request,
                    'Ownership verified. Item marked returned.'
                )

            else:
                messages.error(
                    request,
                    'This item is not currently reserved.'
                )

    return back_to_admin(request)


# ============================================================
# ADMIN - CANCEL BOOKING
# ============================================================

@require_POST
def admin_cancel_booking(request, booking_id):

    if not is_admin(request):
        return redirect('/admin-login/')

    with transaction.atomic():

        booking = get_object_or_404(
            LostItemBooking.objects.select_for_update(),
            pk=booking_id
        )

        if booking.status != 'pending':

            messages.error(
                request,
                'Only pending bookings can be cancelled.'
            )

        else:

            updated = LostItem.objects.filter(
                pk=booking.item_id,
                status='reserved'
            ).update(
                status='available'
            )

            if updated:

                booking.status = 'cancelled'

                booking.save(
                    update_fields=[
                        'status',
                        'updated_at'
                    ]
                )

                messages.success(
                    request,
                    'Booking cancelled; the item is available again.'
                )

            else:
                messages.error(
                    request,
                    'This item is not currently reserved.'
                )

    return back_to_admin(request)
