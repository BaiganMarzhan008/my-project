from django.contrib import admin
from .models import Club, Membership, Notification, Event

@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'leader', 'member_count', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')
    filter_horizontal = ()

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'club', 'status', 'applied_at')
    list_filter = ('status', 'club')
    search_fields = ('user__username', 'club__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'club', 'created_by', 'created_at', 'is_active')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('title', 'content')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'date', 'location')
    list_filter = ('club', 'date')
    search_fields = ('title', 'description')