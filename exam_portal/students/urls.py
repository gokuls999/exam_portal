from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.student_register, name='student_register'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.student_login, name='student_login'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('logout/', views.student_logout, name='student_logout'),
    path('exams/', views.student_exam_list, name='student_exam_list'),
    path('exam/<int:exam_id>/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/snapshot/', views.save_snapshot, name='save_snapshot'),
    path('exam/<int:exam_id>/result/', views.exam_result, name='exam_result'),
]