from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.utils import timezone
from .models import CustomUser
from .forms import CustomUserCreationForm, UserUpdateForm, AdminUserUpdateForm
from clubs.models import Club, Membership, Message, Notification, Event

def is_admin(user):
    return user.is_authenticated and user.is_admin()

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Сіз сәтті тіркелдіңіз!')
                return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
        form.fields['role'].initial = 'user'
    
    return render(request, 'users/register.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Қош келдіңіз, {username}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
        else:
            messages.error(request, 'Қате пайдаланушы аты немесе пароль')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

def user_logout(request):
    logout(request)
    messages.success(request, 'Сіз сәтті шықтыңыз!')
    return redirect('home')

@login_required
def dashboard(request):
    user = request.user
    
    user_memberships = Membership.objects.filter(user=user, status='approved')
    pending_applications = Membership.objects.filter(user=user, status='pending')
    unread_messages = Message.objects.filter(receiver=user, is_read=False).count()

    user_clubs = Club.objects.filter(
        Q(members__user=user, members__status='approved') |
        Q(leader=user)
    ).distinct()
    
    recent_notifications = Notification.objects.filter(
        Q(club__in=user_clubs) | Q(club=None)
    ).filter(is_active=True).order_by('-created_at')[:5]
    
    upcoming_events = Event.objects.filter(
        club__in=user_clubs,
        date__gte=timezone.now()
    ).order_by('date')[:5]
    
    if user.is_admin():
        total_clubs = Club.objects.count()
        total_users = CustomUser.objects.count()
        pending_memberships_count = Membership.objects.filter(status='pending').count()
        active_notifications = Notification.objects.filter(is_active=True).count()
        
        context = {
            'total_clubs': total_clubs,
            'total_users': total_users,
            'pending_memberships_count': pending_memberships_count,
            'active_notifications': active_notifications,
            'recent_users': CustomUser.objects.order_by('-date_joined')[:5],
            'recent_clubs': Club.objects.order_by('-created_at')[:5],
            'user_memberships': user_memberships,
            'pending_applications': pending_applications,
            'unread_messages': unread_messages,
            'recent_notifications': recent_notifications,
            'upcoming_events': upcoming_events,
            'upcoming_events_count': upcoming_events.count(),
        }
        template = 'admin/dashboard.html'
    
    elif user.is_leader():
        led_clubs = Club.objects.filter(leader=user)
        total_members = Membership.objects.filter(club__leader=user, status='approved').count()
        club_events = Event.objects.filter(club__leader=user).count()
        
        context = {
            'led_clubs': led_clubs,
            'total_members': total_members,
            'club_events': club_events,
            'user_memberships': user_memberships,
            'pending_applications': pending_applications,
            'unread_messages': unread_messages,
            'recent_notifications': recent_notifications,
            'upcoming_events': upcoming_events,
            'upcoming_events_count': upcoming_events.count(),
        }
        template = 'users/dashboard.html'  
    
    else:
        context = {
            'user_memberships': user_memberships,
            'pending_applications': pending_applications,
            'unread_messages': unread_messages,
            'recent_notifications': recent_notifications,
            'upcoming_events': upcoming_events,
            'upcoming_events_count': upcoming_events.count(),
        }
        template = 'users/dashboard.html'
    
    return render(request, template, context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль сәтті жаңартылды!')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    user_memberships = Membership.objects.filter(user=request.user, status='approved')
    
    return render(request, 'users/profile.html', {
        'form': form,
        'user_memberships': user_memberships,
    })

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return dashboard(request)

@login_required
@user_passes_test(is_admin)
def user_management(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    active_filter = request.GET.get('active', '')
    
    users = CustomUser.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    if active_filter == 'active':
        users = users.filter(is_active=True)
    elif active_filter == 'inactive':
        users = users.filter(is_active=False)
    
    users = users.order_by('-date_joined')
    
    return render(request, 'admin/user_management.html', {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'active_filter': active_filter,
    })

@login_required
@user_passes_test(is_admin)
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    memberships = Membership.objects.filter(user=user)
    sent_messages = Message.objects.filter(sender=user)[:10]
    received_messages = Message.objects.filter(receiver=user)[:10]
    
    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'{user.username} пайдаланушысы сәтті жаңартылды!')
            return redirect('user_detail', user_id=user.id)
    else:
        form = AdminUserUpdateForm(instance=user)
    
    return render(request, 'admin/user_detail.html', {
        'user': user,
        'form': form,
        'memberships': memberships,
        'sent_messages': sent_messages,
        'received_messages': received_messages,
    })

@login_required
@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'{user.username} пайдаланушысы сәтті құрылды!')
            return redirect('user_management')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'admin/create_user.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'{username} пайдаланушысы сәтті жойылды!')
        return redirect('user_management')
    
    return render(request, 'admin/confirm_delete.html', {
        'object': user,
        'object_name': 'пайдаланушы',
    })