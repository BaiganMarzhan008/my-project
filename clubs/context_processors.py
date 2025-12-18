from .models import Message

def user_clubs(request):
    context = {}
    if request.user.is_authenticated:
        from clubs.models import Club, Membership
        
        user_clubs = Club.objects.filter(
            members__user=request.user,
            members__status='approved'
        ).distinct()

        unread_messages = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        context = {
            'user_clubs': user_clubs,
            'unread_messages': unread_messages,
        }
    return context