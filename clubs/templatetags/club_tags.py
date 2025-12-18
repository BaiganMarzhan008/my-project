from django import template
from clubs.models import Club

register = template.Library()

@register.filter(name='club_count')
def club_count(clubs_or_page, category_id):
    """Клубтар санын санаты бойынша есептеу"""
    if not clubs_or_page:
        return 0

    if hasattr(clubs_or_page, 'object_list'):
        clubs = clubs_or_page.object_list
    else:
        clubs = clubs_or_page
    
    if not hasattr(clubs, 'filter'):
        return 0
    
    return clubs.filter(category=category_id).count()

@register.filter(name='get_category_display')
def get_category_display(category_id):
    """Санаттың көрінетін атауын алу"""
    for cat_id, cat_name in Club.CATEGORY_CHOICES:
        if cat_id == category_id:
            return cat_name
    return category_id

@register.simple_tag
def total_clubs_by_category(category_id):
    """Жалпы клубтар санын санаты бойынша есептеу"""
    return Club.objects.filter(category=category_id).count()

@register.inclusion_tag('clubs/club_stats.html')
def club_statistics():
    """Клубтар статистикасы"""
    return {
        'total_clubs': Club.objects.count(),
        'active_clubs': Club.objects.filter(is_active=True).count(),
        'categories': Club.CATEGORY_CHOICES,
    }