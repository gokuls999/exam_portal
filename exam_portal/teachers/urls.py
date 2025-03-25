from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.teacher_register, name='teacher_register'),
    path('verify-otp/', views.teacher_verify_otp, name='teacher_verify_otp'),
    path('login/', views.teacher_login, name='teacher_login'),
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('create-exam/', views.create_exam, name='create_exam'),
    path('add-questions/<int:exam_id>/', views.add_questions, name='add_questions'),
    path('logout/', views.teacher_logout, name='teacher_logout'),
    path('exam/<int:exam_id>/results/', views.view_exam_results, name='view_exam_results'),
    # Add more paths later
]