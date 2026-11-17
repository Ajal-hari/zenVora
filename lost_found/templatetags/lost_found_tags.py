
from django import template
from lost_found.models import LostItem, LostItemBooking

register = template.Library()


@register.simple_tag(takes_context=True)
def get_lost_found_data(context):

    request = context.get('request')

    if not request or not (request.user.is_authenticated and request.user.is_active and request.user.is_staff):
        return {
            'items': [],
            'bookings': [],
            'total': 0,
            'available': 0,
            'reserved': 0,
            'pending': 0,
        }

    items = LostItem.objects.all().order_by('-created_at')

    bookings = LostItemBooking.objects.select_related(
        'item', 'student'
    ).order_by('-created_at')

    return {
        'items': items,
        'bookings': bookings,
        'total': items.count(),
        'available': items.filter(status='available').count(),
        'reserved': items.filter(status='reserved').count(),
        'pending': bookings.filter(status='pending').count(),
    }
