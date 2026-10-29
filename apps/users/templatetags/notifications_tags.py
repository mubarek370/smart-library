from django import template
from django.core.cache import cache
from apps.users.notifications import get_user_notifications as fetch_notifications

register = template.Library()


@register.simple_tag
def get_user_notifications(user):
    """Get all notifications for a user, cached for 30s to avoid repeated DB roundtrips"""
    if not user or not user.is_authenticated:
        return []
    cache_key = f'user_nav_notifs_{user.id}'
    notifs = cache.get(cache_key)
    if notifs is None:
        notifs = fetch_notifications(user)
        cache.set(cache_key, notifs, 30)
    return notifs


@register.simple_tag
def get_notification_count(user):
    """Get unread notification count, reusing the cached notifications"""
    if not user or not user.is_authenticated:
        return 0
    notifs = get_user_notifications(user)
    return len([n for n in notifs if not n.get('is_read', False)])


@register.simple_tag
def get_pending_requests_count():
    """Get count of pending book requests, cached for 30s"""
    cache_key = 'admin_pending_requests_count'
    count = cache.get(cache_key)
    if count is None:
        from apps.borrow.models import BookRequest
        count = BookRequest.objects.filter(status='pending').count()
        cache.set(cache_key, count, 30)
    return count
