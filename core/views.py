from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
import base64
import binascii
import uuid
from django.http import FileResponse, Http404, JsonResponse
import re

from .models import (
    Student,
    Teacher,
    TeacherAssignment,
    Program,
    Subject,
    Class,
    Attendance,
)

from .face_utils import face_template_from_data_url, face_similarity


def _face_photo_file_from_data_url(image_data):
    """Return a validated JPEG capture as a Django upload file."""
    if not image_data or ',' not in image_data:
        raise ValueError('No captured face photo was received.')

    header, encoded_image = image_data.split(',', 1)
    if not header.lower().startswith('data:image/jpeg;base64'):
        raise ValueError('The captured face photo must be a JPEG image.')

    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (binascii.Error, ValueError) as error:
        raise ValueError('The captured face photo data is invalid.') from error

    if not image_bytes:
        raise ValueError('The captured face photo is empty.')

    return ContentFile(
        image_bytes,
        name=f'{uuid.uuid4().hex}.jpg'
    )


# ==================================================
# HOME
# ==================================================

def home(request):
    return render(request, 'core/home.html')


# ==================================================
# ADMIN LOGIN
# ==================================================

def admin_login(request):

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect('admin_dashboard')

        logout(request)

    if request.method == 'POST':

        username = request.POST.get(
            'adminUsername',
            ''
        ).strip()

        password = request.POST.get(
            'adminPassword',
            ''
        )

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None and user.is_superuser:

            login(request, user)

            return redirect('admin_dashboard')

        return render(
            request,
            'core/adminlogin.html',
            {
                'error': 'Invalid admin username or password.'
            }
        )

    return render(
        request,
        'core/adminlogin.html'
    )


# ==================================================
# ADMIN LOGOUT
# ==================================================

def admin_logout(request):

    logout(request)

    return redirect('admin_login')


# ==================================================
# ADMIN DASHBOARD
# ==================================================

def admin_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    pending_students = Student.objects.filter(
        status='Pending'
    ).select_related(
        'user',
        'program'
    )

    approved_students = Student.objects.filter(
        status='Approved'
    ).select_related(
        'user',
        'program'
    )

    rejected_students = Student.objects.filter(
        status='Rejected'
    ).select_related(
        'user',
        'program'
    )

    pending_teachers = Teacher.objects.filter(
        status='Pending'
    ).select_related('user')

    approved_teachers = Teacher.objects.filter(
        status='Approved'
    ).select_related('user')

    rejected_teachers = Teacher.objects.filter(
        status='Rejected'
    ).select_related('user')

    return render(
        request,
        'core/admindashboard.html',
        {
            'pending_students': pending_students,
            'approved_students': approved_students,
            'rejected_students': rejected_students,

            'pending_student_count': pending_students.count(),
            'approved_student_count': approved_students.count(),
            'rejected_student_count': rejected_students.count(),

            'pending_teachers': pending_teachers,
            'approved_teachers': approved_teachers,
            'rejected_teachers': rejected_teachers,

            'pending_teacher_count': pending_teachers.count(),
            'approved_teacher_count': approved_teachers.count(),
            'rejected_teacher_count': rejected_teachers.count(),
        }
    )


# ==================================================
# VIEW STUDENTS
# ==================================================

def view_students(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    students = Student.objects.select_related(
        'user',
        'program'
    ).all().order_by(
        '-created_at'
    )

    return render(
        request,
        'core/viewstudents.html',
        {
            'students': students
        }
    )


# ==================================================
# DELETE STUDENT
# ==================================================

def delete_student(request, student_id):

    if not request.user.is_authenticated or not request.user.is_superuser:
        if request.user.is_authenticated:
            logout(request)
        return redirect('admin_login')

    # Deletion is intentionally limited to POST requests so it cannot happen
    # just by opening a link.
    if request.method != 'POST':
        return redirect('view_students')

    student = get_object_or_404(
        Student.objects.select_related('user'),
        id=student_id
    )

    linked_user = student.user
    face_storage = student.face_image.storage if student.face_image else None
    face_name = student.face_image.name if student.face_image else None

    # Delete the student and its related records first. If this fails, the
    # stored face photo is left intact.
    student.delete()

    if face_storage and face_name:
        face_storage.delete(face_name)

    # Student accounts are individual accounts, so remove the login too.
    linked_user.delete()

    return redirect('view_students')


# ==================================================
# VIEW TEACHERS
# ==================================================

def view_teachers(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    teachers = Teacher.objects.select_related(
        'user'
    ).prefetch_related(
        'faculty_roles',
        'faculty_roles__program'
    ).all().order_by(
        '-created_at'
    )

    return render(
        request,
        'core/viewteachers.html',
        {
            'teachers': teachers
        }
    )


# ==================================================
# ADMIN-ONLY TEACHER FACE IMAGE
# ==================================================

def admin_teacher_face_image(request, teacher_id):

    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')

    teacher = get_object_or_404(Teacher, id=teacher_id)
    face_image = getattr(teacher, 'face_image', None)

    if not face_image:
        raise Http404('No face photo has been saved for this teacher.')

    return FileResponse(
        face_image.open('rb'),
        content_type='image/jpeg'
    )


# ==================================================
# DELETE TEACHER
# ==================================================

def delete_teacher(request, teacher_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:
        logout(request)
        return redirect('admin_login')

    # Require POST so opening a URL cannot delete an account.
    if request.method != 'POST':
        return redirect('view_teachers')

    teacher = get_object_or_404(
        Teacher.objects.select_related('user'),
        id=teacher_id
    )

    linked_user = teacher.user
    face_image = getattr(teacher, 'face_image', None)
    face_storage = face_image.storage if face_image else None
    face_name = face_image.name if face_image else None

    teacher.delete()

    if face_storage and face_name:
        face_storage.delete(face_name)

    linked_user.delete()

    return redirect('view_teachers')


# ==================================================
# STUDENT REVIEW
# ==================================================

def review_student(request, student_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    student = get_object_or_404(
        Student.objects.select_related(
            'user',
            'program'
        ),
        id=student_id
    )

    return render(
        request,
        'core/reviewstudent.html',
        {
            'student': student
        }
    )


# ==================================================
# ADMIN-ONLY STUDENT FACE IMAGE
# ==================================================

def admin_student_face_image(request, student_id):

    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('admin_login')

    student = get_object_or_404(
        Student,
        id=student_id
    )

    if not student.face_image:
        raise Http404('No face photo has been saved for this student.')

    return FileResponse(
        student.face_image.open('rb'),
        content_type='image/jpeg'
    )


# ==================================================
# STUDENT APPROVAL
# ==================================================

def approve_student(request, student_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    if request.method != 'POST':

        return redirect(
            'review_student',
            student_id=student_id
        )

    student = get_object_or_404(
        Student,
        id=student_id
    )

    if student.status != 'Approved':

        last_student = Student.objects.filter(
            student_id__isnull=False,
            student_id__startswith='STU'
        ).order_by('-id').first()

        if last_student and last_student.student_id:

            try:

                last_number = int(
                    last_student.student_id.replace(
                        'STU',
                        ''
                    )
                )

                next_number = last_number + 1

            except ValueError:

                next_number = 1

        else:

            next_number = 1

        while Student.objects.filter(
            student_id=f'STU{next_number:04d}'
        ).exists():

            next_number += 1

        student.student_id = f'STU{next_number:04d}'
        student.status = 'Approved'
        student.save()

    return redirect('admin_dashboard')


# ==================================================
# STUDENT REJECTION
# ==================================================

def reject_student(request, student_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    if request.method != 'POST':

        return redirect(
            'review_student',
            student_id=student_id
        )

    student = get_object_or_404(
        Student,
        id=student_id
    )

    student.status = 'Rejected'
    student.save()

    return redirect('admin_dashboard')


# ==================================================
# STUDENT LOGIN
# ==================================================

def student_login(request):

    if request.user.is_authenticated:
        try:
            student = Student.objects.get(user=request.user)
            if student.status == 'Approved':
                return redirect('student_dashboard')
        except Student.DoesNotExist:
            pass

        logout(request)

    if request.method == 'POST':
        action = request.POST.get('action', 'login').strip()
        checking_credentials = action == 'check_credentials'

        def login_error(message, status=400):
            if checking_credentials:
                return JsonResponse(
                    {'ok': False, 'message': message},
                    status=status
                )
            return render(
                request,
                'core/studentlogin.html',
                {'error': message}
            )

        student_id = request.POST.get('studentUsername', '').strip()
        password = request.POST.get('studentPassword', '')

        if not student_id or not password:
            return login_error('Enter your Student ID and password.')

        student = Student.objects.select_related('user').filter(
            student_id__iexact=student_id
        ).first()

        # Check the password before processing or comparing any face image.
        if student is None or not student.user.check_password(password):
            return login_error('Student ID or password is incorrect.')

        if student.status != 'Approved':
            return login_error('Your account has not been approved yet.')

        if not student.face_registered or not student.face_encoding:
            return login_error('Face registration is not set up for this account.')

        # This first request only checks credentials. The camera is enabled
        # by the page after this JSON success response.
        if checking_credentials:
            return JsonResponse({
                'ok': True,
                'message': 'Password verified. Face verification is now available.'
            })

        image_data = request.POST.get('image_data', '')
        if not image_data:
            return login_error('Capture your face before attempting to log in.')

        try:
            submitted_encoding = face_template_from_data_url(image_data)
        except (ValueError, RuntimeError) as error:
            return login_error(str(error))

        similarity = face_similarity(
            student.face_encoding,
            submitted_encoding
        )

        # Initial SFace threshold. Calibrate with genuine and non-matching
        # captures before relying on this for real-world access control.
        if similarity < 0.363:
            return login_error('Face verification failed. Please try again.')

        login(request, student.user)
        return redirect('student_dashboard')

    return render(request, 'core/studentlogin.html')
# ==================================================
# STUDENT LOGOUT
# ==================================================

def student_logout(request):

    logout(request)

    return redirect('student_login')


# ==================================================
# STUDENT DASHBOARD
# ==================================================

def student_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('student_login')

    try:

        student = Student.objects.select_related(
            'user',
            'program'
        ).get(
            user=request.user
        )

    except Student.DoesNotExist:

        logout(request)

        return redirect('student_login')

    if student.status != 'Approved':

        logout(request)

        return redirect('student_login')

    return render(
        request,
        'core/studentdashboard.html',
        {
            'student': student
        }
    )


# ==================================================
# STUDENT PROFILE
# ==================================================

def student_profile(request):

    if not request.user.is_authenticated:
        return redirect('student_login')

    try:

        student = Student.objects.select_related(
            'user',
            'program'
        ).get(
            user=request.user
        )

    except Student.DoesNotExist:

        logout(request)

        return redirect('student_login')

    if student.status != 'Approved':

        logout(request)

        return redirect('student_login')

    return render(
        request,
        'core/studentprofile.html',
        {
            'student': student
        }
    )


# ==================================================
# STUDENT-ONLY FACE PHOTO
# ==================================================

def student_face_image(request):

    if not request.user.is_authenticated:
        return redirect('student_login')

    student = get_object_or_404(
        Student,
        user=request.user,
        status='Approved'
    )

    if not student.face_image:
        raise Http404('No face photo has been saved for this account.')

    return FileResponse(
        student.face_image.open('rb'),
        content_type='image/jpeg'
    )


# ==================================================
# STUDENT FACE ENROLLMENT
# ==================================================

def student_face_enroll(request):

    if not request.user.is_authenticated:
        return redirect('student_login')

    try:

        student = Student.objects.get(
            user=request.user
        )

    except Student.DoesNotExist:

        logout(request)

        return redirect('student_login')

    if student.status != 'Approved' or not student.student_id:

        logout(request)

        return redirect('student_login')

    if request.method == 'POST':

        image_data = request.POST.get(
            'image_data',
            ''
        )

        try:

            face_encoding = face_template_from_data_url(
                image_data
            )
            face_image = _face_photo_file_from_data_url(
                image_data
            )

        except (ValueError, RuntimeError, binascii.Error) as error:

            return JsonResponse(
                {
                    'ok': False,
                    'message': str(error)
                },
                status=400
            )

        student.face_encoding = face_encoding
        student.face_image = face_image
        student.face_registered = True
        student.save()

        return JsonResponse(
            {
                'ok': True,
                'message': 'Face enrollment completed.'
            }
        )

    return render(
        request,
        'core/studentfaceenroll.html',
        {
            'student': student
        }
    )


# ==================================================
# STUDENT REGISTRATION
# ==================================================

def student_register(request):
    programs = Program.objects.all().order_by('name')

    if request.method == 'POST':
        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        email = request.POST.get('studentEmail', '').strip()
        phone = request.POST.get('studentPhone', '').strip()
        program_id = request.POST.get('program', '').strip()
        semester = request.POST.get('semester', '').strip()
        password = request.POST.get('studentPassword', '')
        confirm_password = request.POST.get('confirmPassword', '')

        name_pattern = r"^[A-Z][a-zA-Z]*(?:[ '-][A-Za-z]+)*$"

        if not re.match(name_pattern, first_name):
            return render(request, 'core/studentregistration.html', {
                'error': 'First name must start with a capital letter and contain only valid letters.',
                'programs': programs
            })

        if not re.match(name_pattern, last_name):
            return render(request, 'core/studentregistration.html', {
                'error': 'Last name must start with a capital letter and contain only valid letters.',
                'programs': programs
            })

        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'core/studentregistration.html', {
                'error': 'Please enter a valid email address.',
                'programs': programs
            })

        if User.objects.filter(email__iexact=email).exists():
            return render(request, 'core/studentregistration.html', {
                'error': 'An account with this email already exists.',
                'programs': programs
            })

        if not phone.isdigit():
            return render(request, 'core/studentregistration.html', {
                'error': 'Phone number must contain only numbers.',
                'programs': programs
            })

        if len(phone) != 10:
            return render(request, 'core/studentregistration.html', {
                'error': 'Phone number must be exactly 10 digits.',
                'programs': programs
            })

        if not program_id:
            return render(request, 'core/studentregistration.html', {
                'error': 'Please select your program.',
                'programs': programs
            })

        # Accept a numeric Program ID, code, or name.
        if program_id.isdigit():
            program = Program.objects.filter(pk=int(program_id)).first()
        else:
            program = Program.objects.filter(code__iexact=program_id).first()
            if program is None:
                program = Program.objects.filter(name__iexact=program_id).first()

        if program is None:
            return render(request, 'core/studentregistration.html', {
                'error': 'Please select a valid program.',
                'programs': programs
            })

        try:
            semester_number = int(semester)
        except (ValueError, TypeError):
            return render(request, 'core/studentregistration.html', {
                'error': 'Please select a valid semester.',
                'programs': programs
            })

        if semester_number < 1 or semester_number > 8:
            return render(request, 'core/studentregistration.html', {
                'error': 'Please select a valid semester.',
                'programs': programs
            })

        if len(password) < 8:
            return render(request, 'core/studentregistration.html', {
                'error': 'Password must be at least 8 characters long.',
                'programs': programs
            })

        if password != confirm_password:
            return render(request, 'core/studentregistration.html', {
                'error': 'Passwords do not match.',
                'programs': programs
            })

        username = email

        if User.objects.filter(username=username).exists():
            return render(request, 'core/studentregistration.html', {
                'error': 'An account with this email already exists.',
                'programs': programs
            })

        # Create and validate the face template before creating the account.
        image_data = request.POST.get('image_data', '')

        try:
            face_encoding = face_template_from_data_url(image_data)
            face_image = _face_photo_file_from_data_url(image_data)
        except (ValueError, RuntimeError, binascii.Error) as error:
            return render(request, 'core/studentregistration.html', {
                'error': f'Face registration failed: {error}',
                'programs': programs
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )

        Student.objects.create(
            user=user,
            phone=phone,
            program=program,
            semester=semester_number,
            status='Pending',
            face_encoding=face_encoding,
            face_image=face_image,
            face_registered=True
        )

        return render(request, 'core/studentregistration.html', {
            'success': 'Registration submitted successfully. Please wait for administrator approval.',
            'programs': programs
        })

    return render(request, 'core/studentregistration.html', {
        'programs': programs
    })


# ==================================================
# STUDENT REGISTRATION STATUS
# ==================================================

def registration_status(request):

    context = {
        'checked': False
    }

    if request.method == 'POST':

        email = request.POST.get(
            'email',
            ''
        ).strip()

        context['checked'] = True

        try:

            student = Student.objects.select_related(
                'user',
                'program'
            ).get(
                user__email__iexact=email
            )

            context['student'] = student

        except Student.DoesNotExist:

            context['error'] = (
                'No student registration found with this email address.'
            )

    return render(
        request,
        'core/studentregistrationstatus.html',
        context
    )


# ==================================================
# TEACHER LOGIN
# ==================================================

def teacher_login(request):

    # Do not allow an old password-only session to bypass face verification.
    if request.user.is_authenticated:
        try:
            current_teacher = Teacher.objects.get(user=request.user)

            if (
                current_teacher.status == 'Approved'
                and request.session.get('teacher_face_verified')
            ):
                return redirect('teacher_dashboard')

            logout(request)

        except Teacher.DoesNotExist:
            logout(request)

    if request.method != 'POST':
        return render(request, 'core/teacherlogin.html')

    action = request.POST.get('action', 'login').strip()
    checking_credentials = action == 'check_credentials'

    def login_error(message, status=400):
        if checking_credentials:
            return JsonResponse(
                {'ok': False, 'message': message},
                status=status
            )

        return render(
            request,
            'core/teacherlogin.html',
            {'error': message}
        )

    teacher_id = request.POST.get('teacherUsername', '').strip()
    password = request.POST.get('teacherPassword', '')

    if not teacher_id or not password:
        return login_error('Enter your Teacher ID and password.')

    teacher = Teacher.objects.select_related('user').filter(
        teacher_id__iexact=teacher_id
    ).first()

    # Check both credentials before permitting face verification.
    if teacher is None or not teacher.user.check_password(password):
        return login_error('Teacher ID or password is incorrect.')

    if teacher.status != 'Approved':
        return login_error('Your account has not been approved yet.')

    if not teacher.face_registered or not teacher.face_encoding:
        return login_error(
            'Face registration is not set up for this teacher account.'
        )

    # Credential-check requests never create an authenticated session.
    if checking_credentials:
        return JsonResponse({
            'ok': True,
            'message': (
                'Password verified. Face verification is now available.'
            )
        })

    image_data = request.POST.get('image_data', '').strip()

    if not image_data:
        return login_error('Capture your face before attempting to log in.')

    try:
        submitted_encoding = face_template_from_data_url(image_data)
        similarity = face_similarity(
            teacher.face_encoding,
            submitted_encoding
        )
    except (ValueError, RuntimeError, binascii.Error) as error:
        return login_error(f'Face verification failed: {error}')

    if similarity < 0.363:
        return login_error('Face verification failed. Please try again.')

    # Authenticate only after the ID, password, approval, and face all pass.
    login(request, teacher.user)
    request.session['teacher_face_verified'] = True

    return redirect('teacher_dashboard')


# ==================================================
# TEACHER LOGOUT
# ==================================================

def teacher_logout(request):

    logout(request)

    return redirect('teacher_login')


# ==================================================
# TEACHER DASHBOARD
# ==================================================

def teacher_dashboard(request):

    if not request.user.is_authenticated:
        return redirect('teacher_login')

    try:

        teacher = Teacher.objects.select_related(
            'user'
        ).get(
            user=request.user
        )

    except Teacher.DoesNotExist:

        logout(request)

        return redirect('teacher_login')

    if teacher.status != 'Approved':

        logout(request)

        return redirect('teacher_login')

    classes = Class.objects.filter(
        teacher_assignment__teacher=teacher
    ).prefetch_related(
        'students'
    ).order_by(
        'class_name'
    )

    students = Student.objects.filter(
        classes__teacher_assignment__teacher=teacher
    ).distinct().select_related(
        'user',
        'program'
    ).order_by(
        'student_id'
    )

    for student in students:

        attendance_records = Attendance.objects.filter(
            student=student,
            teacher=teacher
        )

        total_attendance = attendance_records.count()

        present_attendance = attendance_records.filter(
            status='Present'
        ).count()

        if total_attendance > 0:

            student.attendance_percentage = round(
                (present_attendance / total_attendance) * 100,
                2
            )

        else:

            student.attendance_percentage = 0

        student.class_name = '--'

        for class_group in classes:

            if class_group.students.filter(
                id=student.id
            ).exists():

                student.class_name = class_group.class_name

                break

    return render(
        request,
        'core/teacherdashboard.html',
        {
            'teacher': teacher,
            'classes': classes,
            'students': students,
            'total_classes': classes.count(),
            'total_students': students.count(),
        }
    )


# ==================================================
# TEACHER PROFILE
# ==================================================

def teacher_profile(request):

    if not request.user.is_authenticated:
        return redirect('teacher_login')

    try:

        teacher = Teacher.objects.select_related(
            'user'
        ).get(
            user=request.user
        )

    except Teacher.DoesNotExist:

        logout(request)

        return redirect('teacher_login')

    if teacher.status != 'Approved':

        logout(request)

        return redirect('teacher_login')

    assignments = TeacherAssignment.objects.filter(
        teacher=teacher
    ).select_related(
        'program'
    ).order_by(
        'program__name',
        'role'
    )

    return render(
        request,
        'core/teacherprofile.html',
        {
            'teacher': teacher,
            'assignments': assignments
        }
    )


# ==================================================
# TEACHER FACE PHOTO FOR THE LOGGED-IN TEACHER
# ==================================================

def teacher_face_image(request):

    if not request.user.is_authenticated:
        return redirect('teacher_login')

    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        logout(request)
        return redirect('teacher_login')

    if teacher.status != 'Approved':
        logout(request)
        return redirect('teacher_login')

    if not teacher.face_image:
        raise Http404('No face photo has been saved for this teacher.')

    return FileResponse(
        teacher.face_image.open('rb'),
        content_type='image/jpeg'
    )


# ==================================================
# TEACHER REGISTRATION
# ==================================================

def teacher_register(request):

    if request.method != 'POST':
        return render(request, 'core/teacherregistration.html')

    first_name = request.POST.get('firstName', '').strip()
    last_name = request.POST.get('lastName', '').strip()
    email = request.POST.get('teacherEmail', '').strip()
    phone = request.POST.get('teacherPhone', '').strip()
    department = request.POST.get('department', '').strip()
    password = request.POST.get('teacherPassword', '')
    confirm_password = request.POST.get('confirmPassword', '')
    image_data = request.POST.get('image_data', '')

    allowed_departments = {
        'BSc CSIT', 'BBA', 'BBS', 'BBM',
        'BCA', 'BHM', 'BIM', 'BIT'
    }
    name_pattern = r"^[A-Z][a-zA-Z]*(?:[ '-][A-Za-z]+)*$"

    if not re.match(name_pattern, first_name):
        return render(request, 'core/teacherregistration.html', {
            'error': 'First name must start with a capital letter and contain only valid letters.'
        })

    if not re.match(name_pattern, last_name):
        return render(request, 'core/teacherregistration.html', {
            'error': 'Last name must start with a capital letter and contain only valid letters.'
        })

    try:
        validate_email(email)
    except ValidationError:
        return render(request, 'core/teacherregistration.html', {
            'error': 'Please enter a valid email address.'
        })

    if User.objects.filter(email__iexact=email).exists():
        return render(request, 'core/teacherregistration.html', {
            'error': 'An account with this email already exists.'
        })

    if not phone.isdigit() or len(phone) != 10:
        return render(request, 'core/teacherregistration.html', {
            'error': 'Phone number must contain exactly 10 digits.'
        })

    if department not in allowed_departments:
        return render(request, 'core/teacherregistration.html', {
            'error': 'Please select a valid department.'
        })

    if len(password) < 8:
        return render(request, 'core/teacherregistration.html', {
            'error': 'Password must be at least 8 characters long.'
        })

    if password != confirm_password:
        return render(request, 'core/teacherregistration.html', {
            'error': 'Passwords do not match.'
        })

    username = email
    if User.objects.filter(username=username).exists():
        return render(request, 'core/teacherregistration.html', {
            'error': 'An account with this email already exists.'
        })

    # Build both the face-matching template and the JPEG photo before
    # creating the account, so invalid face data does not create a user.
    try:
        face_encoding = face_template_from_data_url(image_data)
        face_image = _face_photo_file_from_data_url(image_data)
    except (ValueError, RuntimeError, binascii.Error) as error:
        return render(request, 'core/teacherregistration.html', {
            'error': f'Face registration failed: {error}'
        })

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    Teacher.objects.create(
        user=user,
        phone=phone,
        department=department,
        status='Pending',
        face_encoding=face_encoding,
        face_image=face_image,
        face_registered=True
    )

    return render(request, 'core/teacherregistration.html', {
        'success': (
            'Registration submitted successfully. '
            'Please wait for administrator approval.'
        )
    })


# ==================================================
# TEACHER REGISTRATION STATUS
# ==================================================

def teacher_registration_status(request):

    context = {
        'checked': False
    }

    if request.method == 'POST':

        email = request.POST.get(
            'email',
            ''
        ).strip()

        context['checked'] = True

        try:

            teacher = Teacher.objects.select_related(
                'user'
            ).get(
                user__email__iexact=email
            )

            context['teacher'] = teacher

        except Teacher.DoesNotExist:

            context['error'] = (
                'No teacher registration found with this email address.'
            )

    return render(
        request,
        'core/teacherregistrationstatus.html',
        context
    )


# ==================================================
# TEACHER REVIEW BY ADMIN
# ==================================================

def review_teacher(request, teacher_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    teacher = get_object_or_404(
        Teacher.objects.select_related('user'),
        id=teacher_id
    )

    return render(
        request,
        'core/reviewteacher.html',
        {
            'teacher': teacher
        }
    )


# ==================================================
# TEACHER APPROVAL
# ==================================================

def approve_teacher(request, teacher_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    if request.method != 'POST':

        return redirect(
            'review_teacher',
            teacher_id=teacher_id
        )

    teacher = get_object_or_404(
        Teacher,
        id=teacher_id
    )

    if teacher.status != 'Approved':

        last_teacher = Teacher.objects.filter(
            teacher_id__isnull=False,
            teacher_id__startswith='TCH'
        ).order_by('-id').first()

        if last_teacher and last_teacher.teacher_id:

            try:

                last_number = int(
                    last_teacher.teacher_id.replace(
                        'TCH',
                        ''
                    )
                )

                next_number = last_number + 1

            except ValueError:

                next_number = 1

        else:

            next_number = 1

        while Teacher.objects.filter(
            teacher_id=f'TCH{next_number:04d}'
        ).exists():

            next_number += 1

        teacher.teacher_id = f'TCH{next_number:04d}'
        teacher.status = 'Approved'
        teacher.save()

    return redirect('admin_dashboard')


# ==================================================
# TEACHER REJECTION
# ==================================================

def reject_teacher(request, teacher_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    if request.method != 'POST':

        return redirect(
            'review_teacher',
            teacher_id=teacher_id
        )

    teacher = get_object_or_404(
        Teacher,
        id=teacher_id
    )

    teacher.status = 'Rejected'
    teacher.save()

    return redirect('admin_dashboard')


# ==================================================
# TEACHER - VIEW STUDENT
# ==================================================

def teacher_view_student(request, student_id):

    if not request.user.is_authenticated:
        return redirect('teacher_login')

    try:

        teacher = Teacher.objects.select_related(
            'user'
        ).get(
            user=request.user
        )

    except Teacher.DoesNotExist:

        logout(request)

        return redirect('teacher_login')

    if teacher.status != 'Approved':

        logout(request)

        return redirect('teacher_login')

    student = get_object_or_404(
        Student.objects.select_related(
            'user',
            'program'
        ).filter(
            classes__teacher_assignment__teacher=teacher
        ).distinct(),
        id=student_id
    )

    classes = Class.objects.filter(
        teacher_assignment__teacher=teacher,
        students=student
    ).select_related(
        'program',
        'teacher_assignment',
        'teacher_assignment__program'
    ).order_by(
        'class_name'
    )

    attendance_records = Attendance.objects.filter(
        student=student,
        teacher=teacher
    ).select_related(
        'subject'
    ).order_by(
        '-date'
    )

    total_attendance = attendance_records.count()

    present_attendance = attendance_records.filter(
        status='Present'
    ).count()

    absent_attendance = attendance_records.filter(
        status='Absent'
    ).count()

    late_attendance = attendance_records.filter(
        status='Late'
    ).count()

    if total_attendance > 0:

        attendance_percentage = round(
            (present_attendance / total_attendance) * 100,
            2
        )

    else:

        attendance_percentage = 0

    return render(
        request,
        'core/teacherstudentview.html',
        {
            'teacher': teacher,
            'student': student,
            'classes': classes,
            'attendance_records': attendance_records,
            'total_attendance': total_attendance,
            'present_attendance': present_attendance,
            'absent_attendance': absent_attendance,
            'late_attendance': late_attendance,
            'attendance_percentage': attendance_percentage,
        }
    )


# ==================================================
# ADMIN - MANAGE SUBJECTS
# ==================================================

def manage_subjects(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    programs = Program.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        subject_code = request.POST.get(
            'subject_code',
            ''
        ).strip()

        subject_name = request.POST.get(
            'subject_name',
            ''
        ).strip()

        program_id = request.POST.get(
            'program',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        teacher_id = request.POST.get(
            'teacher',
            ''
        ).strip()

        if not subject_code:
            return redirect('manage_subjects')

        if not subject_name:
            return redirect('manage_subjects')

        if not program_id:
            return redirect('manage_subjects')

        try:

            semester_number = int(semester)

        except (ValueError, TypeError):

            return redirect('manage_subjects')

        if semester_number < 1 or semester_number > 8:
            return redirect('manage_subjects')

        program = get_object_or_404(
            Program,
            id=program_id
        )

        if Subject.objects.filter(
            subject_code__iexact=subject_code
        ).exists():

            return redirect('manage_subjects')

        teacher = None

        if teacher_id:

            teacher = get_object_or_404(
                Teacher,
                id=teacher_id,
                status='Approved'
            )

        Subject.objects.create(
            subject_code=subject_code,
            subject_name=subject_name,
            semester=semester_number,
            program=program,
            teacher=teacher
        )

        return redirect('manage_subjects')

    subjects = Subject.objects.select_related(
        'program',
        'teacher',
        'teacher__user'
    ).all().order_by(
        'program__name',
        'semester',
        'subject_code'
    )

    teachers = Teacher.objects.filter(
        status='Approved'
    ).select_related(
        'user'
    ).order_by(
        'user__first_name',
        'user__last_name'
    )

    return render(
        request,
        'core/adminmanagesubjects.html',
        {
            'subjects': subjects,
            'teachers': teachers,
            'programs': programs,
        }
    )


# ==================================================
# ADMIN - EDIT SUBJECT
# ==================================================

def edit_subject(request, subject_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    subject = get_object_or_404(
        Subject,
        id=subject_id
    )

    programs = Program.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        subject_code = request.POST.get(
            'subject_code',
            ''
        ).strip()

        subject_name = request.POST.get(
            'subject_name',
            ''
        ).strip()

        program_id = request.POST.get(
            'program',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        teacher_id = request.POST.get(
            'teacher',
            ''
        ).strip()

        try:

            semester_number = int(semester)

        except (ValueError, TypeError):

            return redirect('manage_subjects')

        if not subject_code or not subject_name or not program_id:
            return redirect('manage_subjects')

        if semester_number < 1 or semester_number > 8:
            return redirect('manage_subjects')

        if Subject.objects.filter(
            subject_code__iexact=subject_code
        ).exclude(
            id=subject.id
        ).exists():

            return redirect('manage_subjects')

        program = get_object_or_404(
            Program,
            id=program_id
        )

        teacher = None

        if teacher_id:

            teacher = get_object_or_404(
                Teacher,
                id=teacher_id,
                status='Approved'
            )

        subject.subject_code = subject_code
        subject.subject_name = subject_name
        subject.program = program
        subject.semester = semester_number
        subject.teacher = teacher

        subject.save()

        return redirect('manage_subjects')

    teachers = Teacher.objects.filter(
        status='Approved'
    ).select_related(
        'user'
    ).order_by(
        'user__first_name',
        'user__last_name'
    )

    return render(
        request,
        'core/admineditsubject.html',
        {
            'subject': subject,
            'teachers': teachers,
            'programs': programs,
        }
    )


# ==================================================
# ADMIN - DELETE SUBJECT
# ==================================================

def delete_subject(request, subject_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    subject = get_object_or_404(
        Subject,
        id=subject_id
    )

    if request.method == 'POST':
        subject.delete()

    return redirect('manage_subjects')


# ==================================================
# ADMIN - MANAGE CLASSES
# ==================================================

def manage_classes(request):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    programs = Program.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        class_name = request.POST.get(
            'class_name',
            ''
        ).strip()

        program_id = request.POST.get(
            'program',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        section = request.POST.get(
            'section',
            ''
        ).strip()

        teacher_assignment_id = request.POST.get(
            'teacher',
            ''
        ).strip()

        student_ids = request.POST.getlist(
            'students'
        )

        subject_ids = request.POST.getlist(
            'subjects'
        )

        if not class_name:
            return redirect('manage_classes')

        if not program_id:
            return redirect('manage_classes')

        try:

            semester_number = int(semester)

        except (ValueError, TypeError):

            return redirect('manage_classes')

        if semester_number < 1 or semester_number > 8:
            return redirect('manage_classes')

        program = get_object_or_404(
            Program,
            id=program_id
        )

        teacher_assignment = None

        if teacher_assignment_id:

            teacher_assignment = get_object_or_404(
                TeacherAssignment.objects.select_related(
                    'teacher',
                    'program'
                ),
                id=teacher_assignment_id,
                teacher__status='Approved',
                program=program
            )

        class_group = Class.objects.create(
            class_name=class_name,
            program=program,
            semester=semester_number,
            section=section,
            teacher_assignment=teacher_assignment
        )

        students = Student.objects.filter(
            id__in=student_ids,
            status='Approved',
            program=program,
            semester=semester_number
        )

        class_group.students.set(
            students
        )

        subjects = Subject.objects.filter(
            id__in=subject_ids,
            program=program,
            semester=semester_number
        )

        class_group.subjects.set(
            subjects
        )

        return redirect('manage_classes')

    classes = Class.objects.select_related(
        'program',
        'teacher_assignment',
        'teacher_assignment__teacher',
        'teacher_assignment__teacher__user',
        'teacher_assignment__program'
    ).prefetch_related(
        'students',
        'subjects'
    ).all().order_by(
        'program__name',
        'semester',
        'class_name'
    )

    teacher_assignments = TeacherAssignment.objects.filter(
        teacher__status='Approved'
    ).select_related(
        'teacher',
        'teacher__user',
        'program'
    ).order_by(
        'program__name',
        'role',
        'teacher__user__first_name'
    )

    students = Student.objects.filter(
        status='Approved'
    ).select_related(
        'user',
        'program'
    ).order_by(
        'program__name',
        'semester',
        'student_id'
    )

    subjects = Subject.objects.select_related(
        'program'
    ).all().order_by(
        'program__name',
        'semester',
        'subject_code'
    )

    return render(
        request,
        'core/adminmanageclass.html',
        {
            'classes': classes,
            'teacher_assignments': teacher_assignments,
            'students': students,
            'subjects': subjects,
            'programs': programs,
        }
    )


# ==================================================
# ADMIN - EDIT CLASS
# ==================================================

def edit_class(request, class_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    class_group = get_object_or_404(
        Class,
        id=class_id
    )

    programs = Program.objects.all().order_by(
        'name'
    )

    if request.method == 'POST':

        class_name = request.POST.get(
            'class_name',
            ''
        ).strip()

        program_id = request.POST.get(
            'program',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        section = request.POST.get(
            'section',
            ''
        ).strip()

        teacher_assignment_id = request.POST.get(
            'teacher',
            ''
        ).strip()

        student_ids = request.POST.getlist(
            'students'
        )

        subject_ids = request.POST.getlist(
            'subjects'
        )

        try:

            semester_number = int(semester)

        except (ValueError, TypeError):

            return redirect('manage_classes')

        if not class_name or not program_id:
            return redirect('manage_classes')

        if semester_number < 1 or semester_number > 8:
            return redirect('manage_classes')

        program = get_object_or_404(
            Program,
            id=program_id
        )

        teacher_assignment = None

        if teacher_assignment_id:

            teacher_assignment = get_object_or_404(
                TeacherAssignment.objects.select_related(
                    'teacher',
                    'program'
                ),
                id=teacher_assignment_id,
                teacher__status='Approved',
                program=program
            )

        class_group.class_name = class_name
        class_group.program = program
        class_group.semester = semester_number
        class_group.section = section
        class_group.teacher_assignment = teacher_assignment

        class_group.save()

        students = Student.objects.filter(
            id__in=student_ids,
            status='Approved',
            program=program,
            semester=semester_number
        )

        class_group.students.set(
            students
        )

        subjects = Subject.objects.filter(
            id__in=subject_ids,
            program=program,
            semester=semester_number
        )

        class_group.subjects.set(
            subjects
        )

        return redirect('manage_classes')

    teacher_assignments = TeacherAssignment.objects.filter(
        teacher__status='Approved'
    ).select_related(
        'teacher',
        'teacher__user',
        'program'
    ).order_by(
        'program__name',
        'role',
        'teacher__user__first_name'
    )

    students = Student.objects.filter(
        status='Approved'
    ).select_related(
        'user',
        'program'
    ).order_by(
        'program__name',
        'semester',
        'student_id'
    )

    subjects = Subject.objects.select_related(
        'program'
    ).all().order_by(
        'program__name',
        'semester',
        'subject_code'
    )

    return render(
        request,
        'core/admineditclass.html',
        {
            'class_group': class_group,
            'teacher_assignments': teacher_assignments,
            'students': students,
            'subjects': subjects,
            'programs': programs,
        }
    )


# ==================================================
# ADMIN - DELETE CLASS
# ==================================================

def delete_class(request, class_id):

    if not request.user.is_authenticated:
        return redirect('admin_login')

    if not request.user.is_superuser:

        logout(request)

        return redirect('admin_login')

    class_group = get_object_or_404(
        Class,
        id=class_id
    )

    if request.method == 'POST':
        class_group.delete()

    return redirect('manage_classes')
