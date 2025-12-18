from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from clubs import views as club_views

urlpatterns = [

    path('', club_views.home, name='home'),
    
    path('login/', user_views.user_login, name='login'),
    path('logout/', user_views.user_logout, name='logout'),
    path('register/', user_views.register, name='register'),

    path('dashboard/', user_views.dashboard, name='dashboard'),
    path('profile/', user_views.profile, name='profile'),

    path('admin/', user_views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', user_views.user_management, name='user_management'),
    path('admin/users/create/', user_views.create_user, name='create_user'),
    path('admin/users/<int:user_id>/', user_views.user_detail, name='user_detail'),
    path('admin/users/<int:user_id>/delete/', user_views.delete_user, name='delete_user'),
    path('admin/statistics/', club_views.admin_statistics, name='admin_statistics'),
    
    path('', include('clubs.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)