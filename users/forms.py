from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Электрондық пошта')
    first_name = forms.CharField(max_length=30, required=False, label='Аты')
    last_name = forms.CharField(max_length=30, required=False, label='Тегі')
    student_id = forms.CharField(max_length=20, required=False, label='Студенттік номер')
    phone = forms.CharField(max_length=15, required=False, label='Телефон')
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=False, label='Рөл')
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'student_id', 'phone', 'role', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.student_id = self.cleaned_data['student_id']
        user.phone = self.cleaned_data['phone']
        user.role = self.cleaned_data['role']
        
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'student_id', 'phone', 'profile_image']

class AdminUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'student_id', 'phone', 'role', 'is_active', 'is_staff', 'profile_image']