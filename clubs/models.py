from django.db import models
from django.conf import settings
from django.utils import timezone

class Club(models.Model):
    CATEGORY_CHOICES = (
        ('academic', 'Академиялық'),
        ('sports', 'Спорттық'),
        ('cultural', 'Мәдени'),
        ('technical', 'Техникалық'),
        ('art', 'Өнер'),
        ('volunteer', 'Еріктілер'),
        ('other', 'Басқа'),
    )
    
    name = models.CharField(max_length=200, verbose_name="Клуб аты")
    description = models.TextField(verbose_name="Сипаттама")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', verbose_name="Санат")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Құрылған уақыты")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Жаңартылған уақыты")
    logo = models.ImageField(upload_to='club_logos/', blank=True, null=True, verbose_name="Логотип")
    is_active = models.BooleanField(default=True, verbose_name="Белсенді")
    
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_clubs',
        verbose_name="Клуб лидері"
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Клуб"
        verbose_name_plural = "Клубтар"
    
    def __str__(self):
        return self.name
    
    def member_count(self):
        return self.members.filter(status='approved').count()
    
    def get_active_members(self):
        return self.members.filter(status='approved').select_related('user')

class Membership(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Күтуде'),
        ('approved', 'Қабылданған'),
        ('rejected', 'Қабылданбаған'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='club_memberships', verbose_name="Пайдаланушы")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='members', verbose_name="Клуб")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="Мәртебесі")
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="Өтініш берген уақыты")
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Бекітілген уақыты")
    notes = models.TextField(blank=True, null=True, verbose_name="Ескертпелер")
    
    class Meta:
        unique_together = ('user', 'club')
        ordering = ['-applied_at']
        verbose_name = "Мүшелік"
        verbose_name_plural = "Мүшеліктер"
    
    def __str__(self):
        return f"{self.user.username} - {self.club.name} ({self.get_status_display()})"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('announcement', 'Хабарландыру'),
        ('event', 'Іс-шара'),
        ('membership', 'Мүшелік'),
        ('general', 'Жалпы'),
        ('important', 'Маңызды'),
    )
    
    title = models.CharField(max_length=200, verbose_name="Тақырып")
    content = models.TextField(verbose_name="Мазмұны")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='announcement', verbose_name="Түрі")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True, verbose_name="Клуб")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_notifications', verbose_name="Жасаған")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Жасалған уақыты")
    is_active = models.BooleanField(default=True, verbose_name="Белсенді")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Хабарландыру"
        verbose_name_plural = "Хабарландырулар"
    
    def __str__(self):
        return self.title

class Event(models.Model):
    title = models.CharField(max_length=200, verbose_name="Іс-шара аты")
    description = models.TextField(verbose_name="Сипаттама")
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='events', verbose_name="Клуб")
    date = models.DateTimeField(verbose_name="Күні мен уақыты")
    location = models.CharField(max_length=200, verbose_name="Орын")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Құрылған уақыты")
    attendees = models.ManyToManyField(settings.AUTH_USER_MODEL, through='EventAttendance', blank=True, verbose_name="Қатысушылар")
    
    class Meta:
        ordering = ['date']
        verbose_name = "Іс-шара"
        verbose_name_plural = "Іс-шаралар"
    
    def __str__(self):
        return f"{self.title} - {self.club.name}"
    
    def attendee_count(self):
        return self.attendees.count()

class EventAttendance(models.Model):
    ATTENDANCE_CHOICES = (
        ('registered', 'Тіркелген'),
        ('attended', 'Қатысқан'),
        ('absent', 'Қатыспаған'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('event', 'user')
        verbose_name = "Іс-шараға қатысу"
        verbose_name_plural = "Іс-шараға қатысулар"

class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Жіберуші")
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Қабылдаушы")
    subject = models.CharField(max_length=200, verbose_name="Тақырып")
    content = models.TextField(verbose_name="Хабар")
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name="Жіберілген уақыты")
    is_read = models.BooleanField(default=False, verbose_name="Оқылған")
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Хабар"
        verbose_name_plural = "Хабарлар"
    
    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.subject}"