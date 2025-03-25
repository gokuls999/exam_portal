from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Student

class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField()
    name = forms.CharField(max_length=100)
    course = forms.CharField(max_length=100)
    department = forms.CharField(max_length=100)
    register_no = forms.CharField(max_length=20)
   

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'name', 'course', 'department', 'register_no']