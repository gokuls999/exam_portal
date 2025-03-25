from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Teacher, Exam, Question
from students.models import Student, StudentExamSubmission
from students.models import Student  # Import Student for cross-check
import random
from django.core.mail import send_mail
from django.conf import settings
from django.core.files.base import ContentFile
import base64
from django.db import IntegrityError
import face_recognition
import numpy as np
from PIL import Image
from io import BytesIO

def teacher_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        name = request.POST.get('name')
        department = request.POST.get('department')
        course = request.POST.get('course')
        teacher_id = request.POST.get('teacher_id')
        photo1_data = request.POST.get('photo1')
        photo2_data = request.POST.get('photo2')
        photo3_data = request.POST.get('photo3')

        # Validate required fields and password match
        if not all([username, email, password1, password2, name, department, course, teacher_id, photo1_data, photo2_data, photo3_data]):
            return render(request, 'teachers/register.html', {'error': 'All fields and photos are required'})
        if password1 != password2:
            return render(request, 'teachers/register.html', {'error': 'Passwords do not match'})

        # Check for uniqueness
        if User.objects.filter(username=username).exists():
            return render(request, 'teachers/register.html', {'error': 'Username already taken'})
        if Teacher.objects.filter(email=email).exists():
            return render(request, 'teachers/register.html', {'error': 'Email already registered'})
        if Teacher.objects.filter(teacher_id=teacher_id).exists():
            return render(request, 'teachers/register.html', {'error': 'Teacher ID already taken'})

        # Validate photos have faces
        photos = [photo1_data, photo2_data, photo3_data]
        for i, photo_data in enumerate(photos, 1):
            format, imgstr = photo_data.split(';base64,')
            data = base64.b64decode(imgstr)
            img = Image.open(BytesIO(data))
            img_np = np.array(img)
            if not face_recognition.face_encodings(img_np):
                return render(request, 'teachers/register.html', {'error': f'No face detected in Photo {i}'})

        # Generate OTP
        otp = random.randint(100000, 999999)
        request.session['otp'] = otp
        request.session['teacher_data'] = {
            'username': username,
            'email': email,
            'password': password1,
            'name': name,
            'department': department,
            'course': course,
            'teacher_id': teacher_id,
            'photo1_data': photo1_data,
            'photo2_data': photo2_data,
            'photo3_data': photo3_data,
        }

        # Send OTP
        send_mail(
            'OTP for Teacher Registration',
            f'Your OTP is: {otp}',
            'gokulsanil99@gmail.com',
            [email],
            fail_silently=False,
        )

        return redirect('teacher_verify_otp')
    return render(request, 'teachers/register.html')

def teacher_verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')

        if user_otp == str(stored_otp):
            teacher_data = request.session.get('teacher_data')
            try:
                user = User.objects.create_user(
                    username=teacher_data['username'],
                    email=teacher_data['email'],
                    password=teacher_data['password'],
                )

                teacher = Teacher(
                    user=user,
                    name=teacher_data['name'],
                    department=teacher_data['department'],
                    course=teacher_data['course'],
                    teacher_id=teacher_data['teacher_id'],
                    email=teacher_data['email'],
                    is_approved=False
                )

                # Save photos with validation
                for i, photo_key in enumerate(['photo1_data', 'photo2_data', 'photo3_data'], 1):
                    photo_data = teacher_data[photo_key]
                    format, imgstr = photo_data.split(';base64,')
                    ext = format.split('/')[-1]
                    data = base64.b64decode(imgstr)
                    photo_file = ContentFile(data, name=f'{teacher_data["teacher_id"]}_photo{i}.{ext}')
                    getattr(teacher, f'photo{i}').save(photo_file.name, photo_file, save=False)
                
                teacher.save()
                print("Teacher saved successfully:", teacher.id)

                del request.session['otp']
                del request.session['teacher_data']
                return redirect('teacher_login')
            except IntegrityError as e:
                print(f"IntegrityError: {e}")
                return render(request, 'teachers/verify_otp.html', {'error': 'Username, email, or teacher ID already taken'})
            except Exception as e:
                print(f"Error saving teacher: {e}")
                return render(request, 'teachers/verify_otp.html', {'error': f'Error saving data: {str(e)}'})
        else:
            return render(request, 'teachers/verify_otp.html', {'error': 'Invalid OTP'})
    return render(request, 'teachers/verify_otp.html')

def teacher_login(request):
    if request.method == 'POST':
        teacher_id = request.POST.get('teacher_id')
        password = request.POST.get('password')
        photo_data = request.POST.get('photo')

        if not all([teacher_id, password, photo_data]):
            return render(request, 'teachers/login.html', {'error': 'All fields and photo are required'})

        # Check teacher credentials
        try:
            teacher = Teacher.objects.get(teacher_id=teacher_id, is_approved=True)
            if not teacher.user.check_password(password):
                return render(request, 'teachers/login.html', {'error': 'Invalid credentials'})
        except Teacher.DoesNotExist:
            return render(request, 'teachers/login.html', {'error': 'Invalid credentials or not approved'})

        # Decode captured photo
        format, imgstr = photo_data.split(';base64,')
        data = base64.b64decode(imgstr)
        captured_image = Image.open(BytesIO(data))
        captured_image_np = np.array(captured_image)

        # Get captured encoding
        captured_encodings = face_recognition.face_encodings(captured_image_np)
        if not captured_encodings:
            return render(request, 'teachers/login.html', {'error': 'No face detected in captured photo'})
        if len(captured_encodings) > 1:
            return render(request, 'teachers/login.html', {'error': 'Multiple faces detected. Capture one face only.'})
        captured_encoding = captured_encodings[0]

        # Step 1: Compare with target teacher's photos
        stored_images = [
            face_recognition.load_image_file(teacher.photo1.path),
            face_recognition.load_image_file(teacher.photo2.path),
            face_recognition.load_image_file(teacher.photo3.path),
        ]
        stored_encodings = []
        for i, img in enumerate(stored_images, 1):
            encodings = face_recognition.face_encodings(img)
            if encodings:
                stored_encodings.append(encodings[0])
            else:
                print(f"Warning: No face in teacher photo {i} for {teacher_id}")

        if not stored_encodings:
            return render(request, 'teachers/login.html', {'error': 'No valid face data in your registered photos. Contact admin.'})

        matches = face_recognition.compare_faces(stored_encodings, captured_encoding, tolerance=0.45)
        print(f"Matches with {teacher_id}'s photos: {matches}")
        if not any(matches):
            return render(request, 'teachers/login.html', {'error': 'Face does not match your registered photos'})

        # Step 2: Cross-check against all other users
        all_teachers = Teacher.objects.exclude(id=teacher.id)  # Exclude current teacher
        all_students = Student.objects.all()

        other_encodings = []
        for other_teacher in all_teachers:
            for photo_field in [other_teacher.photo1, other_teacher.photo2, other_teacher.photo3]:
                if photo_field:
                    img = face_recognition.load_image_file(photo_field.path)
                    encodings = face_recognition.face_encodings(img)
                    if encodings:
                        other_encodings.append((other_teacher.teacher_id, encodings[0]))

        for student in all_students:
            for photo_field in [student.photo1, student.photo2, student.photo3]:
                if photo_field:
                    img = face_recognition.load_image_file(photo_field.path)
                    encodings = face_recognition.face_encodings(img)
                    if encodings:
                        other_encodings.append((student.register_no, encodings[0]))

        if other_encodings:
            other_matches = face_recognition.compare_faces([enc for _, enc in other_encodings], captured_encoding, tolerance=0.45)
            matched_users = [user_id for (user_id, _), match in zip(other_encodings, other_matches) if match]
            print(f"Cross-check matches with other users: {matched_users}")
            if any(other_matches):
                return render(request, 'teachers/login.html', {'error': f'Face matches another user ({", ".join(matched_users)}). Login denied.'})

        # Login successful
        request.session['teacher_id'] = teacher.id
        return redirect('teacher_dashboard')

    return render(request, 'teachers/login.html')

def teacher_dashboard(request):
    if 'teacher_id' not in request.session:
        return redirect('teacher_login')
    teacher = Teacher.objects.get(id=request.session['teacher_id'])
    exams = Exam.objects.filter(teacher=teacher)
    return render(request, 'teachers/dashboard.html', {'teacher': teacher, 'exams': exams})

def create_exam(request):
    if 'teacher_id' not in request.session:
        return redirect('teacher_login')
    teacher = Teacher.objects.get(id=request.session['teacher_id'])

    if request.method == 'POST':
        course = request.POST.get('course')
        department = request.POST.get('department')
        time_limit = request.POST.get('time_limit')

        if not all([course, department, time_limit]):
            return render(request, 'teachers/create_exam.html', {'error': 'All fields are required'})

        exam = Exam(
            teacher=teacher,
            course=course,
            department=department,
            time_limit=int(time_limit)
        )
        exam.save()
        return redirect('add_questions', exam_id=exam.id)

    return render(request, 'teachers/create_exam.html', {'teacher': teacher})

def add_questions(request, exam_id):
    if 'teacher_id' not in request.session:
        return redirect('teacher_login')
    teacher = Teacher.objects.get(id=request.session['teacher_id'])
    try:
        exam = Exam.objects.get(id=exam_id, teacher=teacher)
    except Exam.DoesNotExist:
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        text = request.POST.get('text')
        option_a = request.POST.get('option_a')
        option_b = request.POST.get('option_b')
        option_c = request.POST.get('option_c')
        option_d = request.POST.get('option_d')
        correct_answer = request.POST.get('correct_answer')
        marks_correct = request.POST.get('marks_correct', 1)
        marks_wrong = request.POST.get('marks_wrong', 0)

        if not all([text, option_a, option_b, option_c, option_d, correct_answer]):
            return render(request, 'teachers/add_questions.html', {'exam': exam, 'error': 'All fields are required'})

        Question.objects.create(
            exam=exam,
            text=text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            marks_correct=int(marks_correct),
            marks_wrong=int(marks_wrong)
        )
        return redirect('add_questions', exam_id=exam.id)  # Stay on page to add more questions

    questions = Question.objects.filter(exam=exam)
    return render(request, 'teachers/add_questions.html', {'exam': exam, 'questions': questions})

def teacher_logout(request):
    if 'teacher_id' in request.session:
        del request.session['teacher_id']
    return redirect('teacher_login')

# ... (other imports and views remain unchanged until teacher_logout)

def view_exam_results(request, exam_id):
    if 'teacher_id' not in request.session:
        return redirect('teacher_login')
    teacher = Teacher.objects.get(id=request.session['teacher_id'])
    
    try:
        exam = Exam.objects.get(id=exam_id, teacher=teacher)
    except Exam.DoesNotExist:
        return redirect('teacher_dashboard')

    # Get all submissions for this exam
    submissions = StudentExamSubmission.objects.filter(exam=exam).select_related('student')
    
    return render(request, 'teachers/exam_results.html', {
        'teacher': teacher,
        'exam': exam,
        'submissions': submissions
    })