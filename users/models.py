from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Электрондық пошта міндетті')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпайдаланушы is_staff=True болуы керек')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпайдаланушы is_superuser=True болуы керек')
        
        return self.create_user(username, email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Админ'),
        ('leader', 'Клуб лидері'),
        ('member', 'Мүше'),
        ('user', 'Пайдаланушы'),
    )
    
    username = models.CharField(max_length=150, unique=True, verbose_name="Пайдаланушы аты")
    email = models.EmailField(unique=True, verbose_name="Электрондық пошта")
    first_name = models.CharField(max_length=30, blank=True, verbose_name="Аты")
    last_name = models.CharField(max_length=30, blank=True, verbose_name="Тегі")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user', verbose_name="Рөлі")
    student_id = models.CharField(max_length=20, blank=True, null=True, verbose_name="Студенттік номер")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="Телефон")
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="Профиль суреті")
    
    is_active = models.BooleanField(default=True, verbose_name="Белсенді")
    is_staff = models.BooleanField(default=False, verbose_name="Қызметші")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Тіркелген күні")
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
    
    def is_leader(self):
        return self.role == 'leader'
    
    def is_member(self):
        return self.role == 'member'
    
    class Meta:
        verbose_name = "Пайдаланушы"
        verbose_name_plural = "Пайдаланушылар"