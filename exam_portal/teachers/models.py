from django.db import models
from django.contrib.auth.models import User

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    course = models.CharField(max_length=100)
    teacher_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    is_approved = models.BooleanField(default=False)
    photo1 = models.ImageField(upload_to='teacher_photos/')
    photo2 = models.ImageField(upload_to='teacher_photos/')
    photo3 = models.ImageField(upload_to='teacher_photos/')

    def __str__(self):
        return self.name

class Exam(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    time_limit = models.IntegerField(help_text="Time in minutes")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Exam for {self.course} - {self.department}"

class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    text = models.TextField()
    option_a = models.CharField(max_length=200)
    option_b = models.CharField(max_length=200)
    option_c = models.CharField(max_length=200)
    option_d = models.CharField(max_length=200)
    correct_answer = models.CharField(max_length=1, choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')])
    marks_correct = models.IntegerField(default=1)
    marks_wrong = models.IntegerField(default=0)

    def __str__(self):
        return self.text[:50]