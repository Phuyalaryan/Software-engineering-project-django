from django.urls import path
from . import views


urlpatterns = [

    # ==================================================
    # HOME
    # ==================================================

    path(
        '',
        views.home,
        name='home'
    ),


    # ==================================================
    # ADMIN LOGIN
    # ==================================================

    path(
        'admin-login/',
        views.admin_login,
        name='admin_login'
    ),


    # ==================================================
    # ADMIN LOGOUT
    # ==================================================

    path(
        'admin-logout/',
        views.admin_logout,
        name='admin_logout'
    ),


    # ==================================================
    # ADMIN DASHBOARD
    # ==================================================

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),


    # ==================================================
    # VIEW STUDENTS
    # ==================================================

    path(
        'admin-dashboard/students/',
        views.view_students,
        name='view_students'
    ),


    # ==================================================
    # VIEW TEACHERS
    # ==================================================

    path(
        'admin-dashboard/teachers/',
        views.view_teachers,
        name='view_teachers'
    ),


    # ==================================================
    # STUDENT REVIEW
    # ==================================================

    path(
        'admin-dashboard/student/<int:student_id>/review/',
        views.review_student,
        name='review_student'
    ),


    # ==================================================
    # STUDENT FACE PHOTO FOR ADMIN REVIEW
    # ==================================================

    path(
        'admin-dashboard/student/<int:student_id>/face/',
        views.admin_student_face_image,
        name='admin_student_face_image'
    ),


    # ==================================================
    # STUDENT APPROVAL
    # ==================================================

    path(
        'admin-dashboard/student/<int:student_id>/approve/',
        views.approve_student,
        name='approve_student'
    ),


    # ==================================================
    # STUDENT REJECTION
    # ==================================================

    path(
        'admin-dashboard/student/<int:student_id>/reject/',
        views.reject_student,
        name='reject_student'
    ),


    # ==================================================
    # DELETE STUDENT
    # ==================================================

    path(
        'admin-dashboard/student/<int:student_id>/delete/',
        views.delete_student,
        name='delete_student'
    ),


    # ==================================================
    # STUDENT LOGIN
    # ==================================================

    path(
        'student-login/',
        views.student_login,
        name='student_login'
    ),


    # ==================================================
    # STUDENT LOGOUT
    # ==================================================

    path(
        'student-logout/',
        views.student_logout,
        name='student_logout'
    ),


    # ==================================================
    # STUDENT DASHBOARD
    # ==================================================

    path(
        'student-dashboard/',
        views.student_dashboard,
        name='student_dashboard'
    ),


    # ==================================================
    # STUDENT PROFILE
    # ==================================================

    path(
        'student-profile/',
        views.student_profile,
        name='student_profile'
    ),


    # ==================================================
    # STUDENT FACE PHOTO FOR THE LOGGED-IN STUDENT
    # ==================================================

    path(
        'student-profile/face/',
        views.student_face_image,
        name='student_face_image'
    ),


    # ==================================================
    # STUDENT FACE ENROLLMENT
    # ==================================================

    path(
        'student-face-enroll/',
        views.student_face_enroll,
        name='student_face_enroll'
    ),


    # ==================================================
    # STUDENT REGISTRATION
    # ==================================================

    path(
        'student-register/',
        views.student_register,
        name='student_register'
    ),


    # ==================================================
    # STUDENT REGISTRATION STATUS
    # ==================================================

    path(
        'registration-status/',
        views.registration_status,
        name='registration_status'
    ),


    # ==================================================
    # TEACHER LOGIN
    # ==================================================

    path(
        'teacher-login/',
        views.teacher_login,
        name='teacher_login'
    ),


    # ==================================================
    # TEACHER LOGOUT
    # ==================================================

    path(
        'teacher-logout/',
        views.teacher_logout,
        name='teacher_logout'
    ),


    # ==================================================
    # TEACHER DASHBOARD
    # ==================================================

    path(
        'teacher-dashboard/',
        views.teacher_dashboard,
        name='teacher_dashboard'
    ),


    # ==================================================
    # TEACHER VIEW STUDENT
    # ==================================================

    path(
        'teacher-dashboard/student/<int:student_id>/',
        views.teacher_view_student,
        name='teacher_view_student'
    ),


    # ==================================================
    # TEACHER PROFILE
    # ==================================================

    path(
        'teacher-profile/',
        views.teacher_profile,
        name='teacher_profile'
    ),


    # ==================================================
    # TEACHER FACE PHOTO FOR THE LOGGED-IN TEACHER
    # ==================================================

    path(
        'teacher-profile/face/',
        views.teacher_face_image,
        name='teacher_face_image'
    ),


    # ==================================================
    # TEACHER REGISTRATION
    # ==================================================

    path(
        'teacher-register/',
        views.teacher_register,
        name='teacher_register'
    ),


    # ==================================================
    # TEACHER REGISTRATION STATUS
    # ==================================================

    path(
        'teacher-registration-status/',
        views.teacher_registration_status,
        name='teacher_registration_status'
    ),


    # ==================================================
    # TEACHER REVIEW BY ADMIN
    # ==================================================

    path(
        'admin-dashboard/teacher/<int:teacher_id>/review/',
        views.review_teacher,
        name='review_teacher'
    ),


    # ==================================================
    # TEACHER FACE PHOTO FOR ADMIN REVIEW
    # ==================================================

    path(
        'admin-dashboard/teacher/<int:teacher_id>/face/',
        views.admin_teacher_face_image,
        name='admin_teacher_face_image'
    ),


    # ==================================================
    # DELETE TEACHER
    # ==================================================

    path(
        'admin-dashboard/teacher/<int:teacher_id>/delete/',
        views.delete_teacher,
        name='delete_teacher'
    ),


    # ==================================================
    # TEACHER APPROVAL
    # ==================================================

    path(
        'admin-dashboard/teacher/<int:teacher_id>/approve/',
        views.approve_teacher,
        name='approve_teacher'
    ),


    # ==================================================
    # TEACHER REJECTION
    # ==================================================

    path(
        'admin-dashboard/teacher/<int:teacher_id>/reject/',
        views.reject_teacher,
        name='reject_teacher'
    ),


    # ==================================================
    # MANAGE SUBJECTS
    # ==================================================

    path(
        'admin-dashboard/subjects/',
        views.manage_subjects,
        name='manage_subjects'
    ),


    # ==================================================
    # EDIT SUBJECT
    # ==================================================

    path(
        'admin-dashboard/subjects/<int:subject_id>/edit/',
        views.edit_subject,
        name='edit_subject'
    ),


    # ==================================================
    # DELETE SUBJECT
    # ==================================================

    path(
        'admin-dashboard/subjects/<int:subject_id>/delete/',
        views.delete_subject,
        name='delete_subject'
    ),


    # ==================================================
    # MANAGE CLASSES
    # ==================================================

    path(
        'admin-dashboard/classes/',
        views.manage_classes,
        name='manage_classes'
    ),


    # ==================================================
    # EDIT CLASS
    # ==================================================

    path(
        'admin-dashboard/classes/<int:class_id>/edit/',
        views.edit_class,
        name='edit_class'
    ),


    # ==================================================
    # DELETE CLASS
    # ==================================================

    path(
        'admin-dashboard/classes/<int:class_id>/delete/',
        views.delete_class,
        name='delete_class'
    ),

]