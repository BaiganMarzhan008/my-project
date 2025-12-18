from django.urls import path
from . import views

urlpatterns = [
    path('clubs/', views.club_list, name='club_list'),
    path('clubs/create/', views.club_create, name='club_create'),
    path('clubs/<int:pk>/', views.club_detail, name='club_detail'),
    path('clubs/<int:pk>/update/', views.club_update, name='club_update'),
    path('clubs/<int:pk>/delete/', views.club_delete, name='club_delete'),
    path('clubs/<int:pk>/apply/', views.apply_membership, name='apply_membership'),
    path('clubs/<int:pk>/manage-memberships/', views.manage_memberships, name='manage_memberships'),
    
    path('notifications/', views.notifications, name='notifications'),
    path('notification/create/', views.create_notification, name='create_notification'),
    
    path('events/', views.events, name='events'),
    path('event/create/', views.create_event, name='create_event'),
    path('event/create/<int:pk>/', views.create_event, name='create_event_for_club'),
    
    path('my-clubs/', views.my_clubs, name='my_clubs'),
    
    path('messages/', views.inbox, name='inbox'),
    path('messages/send/', views.send_message, name='send_message'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
]