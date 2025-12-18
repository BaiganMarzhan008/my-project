from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import Club, Membership, Notification, Event, Message
from .forms import ClubForm, MembershipForm, NotificationForm, EventForm, MessageForm
from users.models import CustomUser

def is_admin(user):
    return user.is_authenticated and user.is_admin()

def is_leader(user):
    return user.is_authenticated and (user.is_leader() or user.is_admin())

def home(request):
    clubs = Club.objects.filter(is_active=True)[:6]
    notifications = Notification.objects.filter(is_active=True).order_by('-created_at')[:5]
    upcoming_events = Event.objects.filter(date__gte=timezone.now()).order_by('date')[:3]
    
    context = {
        'clubs': clubs,
        'notifications': notifications,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'clubs/home.html', context)

@login_required
def club_list(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    clubs = Club.objects.all()
    
    if search_query:
        clubs = clubs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_filter:
        clubs = clubs.filter(category=category_filter)
    
    if not request.user.is_admin():
        clubs = clubs.filter(is_active=True)
    
    categories = Club.CATEGORY_CHOICES
    
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(clubs, 9)  
    page = request.GET.get('page', 1)
    
    try:
        clubs = paginator.page(page)
    except PageNotAnInteger:
        clubs = paginator.page(1)
    except EmptyPage:
        clubs = paginator.page(paginator.num_pages)
    
    return render(request, 'clubs/club_list.html', {
        'clubs': clubs,
        'categories': categories,
        'search_query': search_query,
        'category_filter': category_filter,
    })

@login_required
@user_passes_test(is_admin)
def club_create(request):
    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES)
        if form.is_valid():
            club = form.save()
            messages.success(request, f'"{club.name}" клубы сәтті құрылды!')
            return redirect('club_detail', pk=club.pk)
    else:
        form = ClubForm()
    
    return render(request, 'clubs/club_form.html', {'form': form, 'action': 'Құру'})

@login_required
def club_detail(request, pk):
    club = get_object_or_404(Club, pk=pk)
    
    if not club.is_active and not request.user.is_admin():
        messages.error(request, 'Бұл клуб белсенді емес')
        return redirect('club_list')
    
    is_member = False
    membership = None
    if request.user.is_authenticated:
        membership = Membership.objects.filter(user=request.user, club=club).first()
        if membership and membership.status == 'approved':
            is_member = True
    
    notifications = club.notifications.filter(is_active=True).order_by('-created_at')[:10]
    events = club.events.all().order_by('date')
    members = club.get_active_members()
    
    can_edit = request.user.is_admin() or (request.user == club.leader)
    can_post = can_edit or is_member
    
    return render(request, 'clubs/club_detail.html', {
        'club': club,
        'is_member': is_member,
        'membership': membership,
        'notifications': notifications,
        'events': events,
        'members': members,
        'can_edit': can_edit,
        'can_post': can_post,
    })

@login_required
@user_passes_test(is_admin)
def club_update(request, pk):
    club = get_object_or_404(Club, pk=pk)
    
    if request.method == 'POST':
        form = ClubForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{club.name}" клубы сәтті жаңартылды!')
            return redirect('club_detail', pk=club.pk)
    else:
        form = ClubForm(instance=club)
    
    return render(request, 'clubs/club_form.html', {'form': form, 'action': 'Жаңарту', 'club': club})

@login_required
@user_passes_test(is_admin)
def club_delete(request, pk):
    club = get_object_or_404(Club, pk=pk)
    
    if request.method == 'POST':
        club_name = club.name
        club.delete()
        messages.success(request, f'"{club_name}" клубы сәтті жойылды!')
        return redirect('club_list')
    
    return render(request, 'clubs/confirm_delete.html', {'club': club})

@login_required
def apply_membership(request, pk):
    club = get_object_or_404(Club, pk=pk)
    
    if not club.is_active:
        messages.error(request, 'Бұл клуб белсенді емес')
        return redirect('club_list')
    
    existing_membership = Membership.objects.filter(user=request.user, club=club).first()
    if existing_membership:
        messages.warning(request, f'Сіз бұл клубқа қазірдің өзінде өтініш бергенсіз. Мәртебе: {existing_membership.get_status_display()}')
        return redirect('club_detail', pk=pk)
    
    membership = Membership.objects.create(
        user=request.user,
        club=club,
        status='pending'
    )
    
    messages.success(request, f'Сіз "{club.name}" клубына мүше болу үшін өтініш бердіңіз!')
    return redirect('club_detail', pk=pk)

@login_required
def manage_memberships(request, pk):
    club = get_object_or_404(Club, pk=pk)
    
    if not (request.user == club.leader or request.user.is_admin()):
        messages.error(request, 'Сізде бұл клубты басқару құқығы жоқ')
        return redirect('club_detail', pk=pk)  
    
    pending_memberships = Membership.objects.filter(club=club, status='pending')
    approved_memberships = Membership.objects.filter(club=club, status='approved')
    rejected_memberships = Membership.objects.filter(club=club, status='rejected')
    
    if request.method == 'POST':
        membership_id = request.POST.get('membership_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if membership_id and action:
            membership = get_object_or_404(Membership, id=membership_id, club=club)
            
            if action == 'approve':
                membership.status = 'approved'
                membership.approved_at = timezone.now()
                membership.notes = notes
                membership.save()
                
                user = membership.user
                if user.role == 'user':
                    user.role = 'member'
                    user.save()
                
                messages.success(request, f'{membership.user.username} мүшелігі қабылданды!')
                
            elif action == 'reject':
                membership.status = 'rejected'
                membership.notes = notes
                membership.save()
                messages.success(request, f'{membership.user.username} мүшелігі қабылданбады деп таңдалды!')
    
    return render(request, 'clubs/manage_memberships.html', {
        'club': club,
        'pending_memberships': pending_memberships,
        'approved_memberships': approved_memberships,
        'rejected_memberships': rejected_memberships,
    })

@login_required
def create_notification(request):
    user_clubs = Club.objects.filter(
        Q(leader=request.user) | 
        Q(members__user=request.user, members__status='approved')
    ).distinct()
    
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()
            messages.success(request, 'Хабарландыру сәтті жарияланды!')
            return redirect('club_detail', pk=notification.club.pk if notification.club else 0)
    else:
        form = NotificationForm()
        if not request.user.is_admin():
            form.fields['club'].queryset = user_clubs
    
    return render(request, 'clubs/notification_form.html', {'form': form})

@login_required
def create_event(request, pk=None):
    club = None
    if pk:
        club = get_object_or_404(Club, pk=pk)
    
    user_clubs = Club.objects.filter(
        Q(leader=request.user) | 
        Q(members__user=request.user, members__status='approved') |
        Q(is_active=True)
    ).distinct()
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Іс-шара сәтті құрылды!')
            return redirect('club_detail', pk=event.club.pk)
    else:
        form = EventForm()
        if not request.user.is_admin():
            form.fields['club'].queryset = user_clubs
        if club:
            form.fields['club'].initial = club
    
    return render(request, 'clubs/event_form.html', {'form': form, 'club': club})

@login_required
def my_clubs(request):
    memberships = Membership.objects.filter(
        user=request.user,
        status='approved'
    ).select_related('club')
    
    led_clubs = Club.objects.filter(leader=request.user)
    pending_applications = Membership.objects.filter(user=request.user, status='pending')
    
    return render(request, 'clubs/my_clubs.html', {
        'memberships': memberships,
        'led_clubs': led_clubs,
        'pending_applications': pending_applications,
    })

@login_required
def notifications(request):
    user_clubs = Club.objects.filter(
        Q(leader=request.user) | 
        Q(members__user=request.user, members__status='approved')
    ).distinct()
    
    all_notifications = Notification.objects.filter(
        Q(club__in=user_clubs) | Q(club=None)
    ).filter(is_active=True).order_by('-created_at')
    
    return render(request, 'clubs/notifications.html', {
        'notifications': all_notifications,
    })

@login_required
def events(request):
    user_clubs = Club.objects.filter(
        Q(leader=request.user) | 
        Q(members__user=request.user, members__status='approved')
    ).distinct()
    
    upcoming_events = Event.objects.filter(
        club__in=user_clubs,
        date__gte=timezone.now()
    ).order_by('date')
    
    past_events = Event.objects.filter(
        club__in=user_clubs,
        date__lt=timezone.now()
    ).order_by('-date')[:10]
    
    return render(request, 'clubs/events.html', {
        'upcoming_events': upcoming_events,
        'past_events': past_events,
    })

@login_required
def send_message(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.save()
            messages.success(request, 'Хабар сәтті жіберілді!')
            return redirect('inbox')
    else:
        form = MessageForm()
    
    return render(request, 'clubs/send_message.html', {'form': form})

@login_required
def inbox(request):
    received_messages = Message.objects.filter(receiver=request.user).order_by('-sent_at')
    sent_messages = Message.objects.filter(sender=request.user).order_by('-sent_at')
    
    unread_messages = received_messages.filter(is_read=False)
    for message in unread_messages:
        message.is_read = True
        message.save()
    
    return render(request, 'clubs/inbox.html', {
        'received_messages': received_messages,
        'sent_messages': sent_messages,
    })

@login_required
def message_detail(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    if message.sender != request.user and message.receiver != request.user:
        messages.error(request, 'Сізде бұл хабарды көру құқығы жоқ')
        return redirect('inbox')
    
    if message.receiver == request.user and not message.is_read:
        message.is_read = True
        message.save()
    
    return render(request, 'clubs/message_detail.html', {'message': message})



@login_required
@user_passes_test(is_admin)
def admin_statistics(request):
    try:

        total_clubs = Club.objects.count()
        active_clubs = Club.objects.filter(is_active=True).count()
        total_users = CustomUser.objects.count()
        total_memberships = Membership.objects.count()
        approved_memberships = Membership.objects.filter(status='approved').count()

        clubs_by_category = Club.objects.values('category').annotate(count=Count('id')).order_by('-count')

        categories_data = []
        for item in clubs_by_category:
            category_data = {
                'category': item['category'] if item['category'] else 'other',
                'count': item['count']
            }
            categories_data.append(category_data)
        

        memberships_by_status = Membership.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        

        seven_days_ago = timezone.now() - timedelta(days=7)
        new_users_week = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()
        new_memberships_week = Membership.objects.filter(applied_at__gte=seven_days_ago).count()
        new_notifications_week = Notification.objects.filter(created_at__gte=seven_days_ago).count()

        admin_count = CustomUser.objects.filter(role='admin').count()
        leader_count = CustomUser.objects.filter(role='leader').count()
        member_count = CustomUser.objects.filter(role='member').count()
        user_count = CustomUser.objects.filter(role='user').count()
        

        total_by_roles = admin_count + leader_count + member_count + user_count
        
        context = {
            'total_clubs': total_clubs,
            'active_clubs': active_clubs,
            'total_users': total_users,
            'total_memberships': total_memberships,
            'approved_memberships': approved_memberships,
            'clubs_by_category': categories_data,
            'memberships_by_status': list(memberships_by_status),
            'new_users_week': new_users_week,
            'new_memberships_week': new_memberships_week,
            'new_notifications_week': new_notifications_week,
            'admin_count': admin_count,
            'leader_count': leader_count,
            'member_count': member_count,
            'user_count': user_count,
            'total_by_roles': total_by_roles,  
        }
        
    except Exception as e:

        print(f"Статистика қатесі: {e}")
        context = {
            'total_clubs': 0,
            'active_clubs': 0,
            'total_users': 0,
            'total_memberships': 0,
            'approved_memberships': 0,
            'clubs_by_category': [],
            'memberships_by_status': [],
            'new_users_week': 0,
            'new_memberships_week': 0,
            'new_notifications_week': 0,
            'admin_count': 0,
            'leader_count': 0,
            'member_count': 0,
            'user_count': 0,
            'total_by_roles': 0,
        }
    
    return render(request, 'admin/statistics.html', context)