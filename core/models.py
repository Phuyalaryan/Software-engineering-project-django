from django.db import models
from django.contrib.auth.models import User


# =========================================================
# PROGRAM
# =========================================================

class Program(models.Model):

    name = models.CharField(
        max_length=100,
        unique=True
    )

    code = models.CharField(
        max_length=20,
        unique=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} ({self.code})"


# =========================================================
# STUDENT
# =========================================================

class Student(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    student_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name='students'
    )

    semester = models.PositiveIntegerField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    face_registered = models.BooleanField(
        default=False
    )

    face_encoding = models.JSONField(
        null=True,
        blank=True
    )

    face_image = models.ImageField(
        upload_to='student_faces/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.student_id or 'Not Assigned'} - "
            f"{self.user.get_full_name()}"
        )


# =========================================================
# TEACHER
# =========================================================

class Teacher(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile'
    )

    teacher_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True
    )

    phone = models.CharField(
        max_length=15
    )

    department = models.CharField(
        max_length=100
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    face_registered = models.BooleanField(
        default=False
    )

    face_encoding = models.JSONField(
        null=True,
        blank=True
    )

    face_image = models.ImageField(
        upload_to='teacher_faces/',
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"{self.teacher_id or 'Not Assigned'} - "
            f"{self.user.get_full_name()}"
        )


# =========================================================
# TEACHER FACULTY / ROLE ASSIGNMENT
# =========================================================

class TeacherAssignment(models.Model):

    ROLE_CHOICES = [
        ('HOD', 'HOD'),
        ('Lecturer', 'Lecturer'),
        ('Practical Instructor', 'Practical Instructor'),
        ('Lab Instructor', 'Lab Instructor'),
        ('Assistant Lecturer', 'Assistant Lecturer'),
        ('Coordinator', 'Coordinator'),
    ]

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='faculty_roles'
    )

    # Nullable temporarily so existing database records
    # can be migrated safely.
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
        null=True,
        blank=True
    )

    faculty = models.CharField(
        max_length=100
    )

    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            'teacher',
            'program',
            'faculty',
            'role'
        )

        ordering = [
            'program',
            'faculty',
            'role'
        ]

    def __str__(self):
        program_name = (
            self.program.name
            if self.program
            else 'No Program'
        )

        return (
            f"{program_name} - "
            f"{self.faculty} - "
            f"{self.get_role_display()} - "
            f"{self.teacher.user.get_full_name()}"
        )


# =========================================================
# SUBJECT
# =========================================================

class Subject(models.Model):

    subject_code = models.CharField(
        max_length=20,
        unique=True
    )

    subject_name = models.CharField(
        max_length=100
    )

    semester = models.PositiveIntegerField()

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='subjects'
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subjects'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.subject_code} - {self.subject_name}"


# =========================================================
# CLASS
# =========================================================

class Class(models.Model):

    class_name = models.CharField(
        max_length=100
    )

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name='classes'
    )

    semester = models.PositiveIntegerField()

    section = models.CharField(
        max_length=20,
        blank=True
    )

    teacher_assignment = models.ForeignKey(
        TeacherAssignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classes'
    )

    students = models.ManyToManyField(
        Student,
        related_name='classes',
        blank=True
    )

    subjects = models.ManyToManyField(
        Subject,
        related_name='classes',
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.class_name


# =========================================================
# ATTENDANCE
# =========================================================

class Attendance(models.Model):

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attendance_records'
    )

    date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES
    )

    method = models.CharField(
        max_length=30,
        default='Manual'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.date} - "
            f"{self.status}"
        )


# =========================================================
# GRADE
# =========================================================

class Grade(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='grades'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades'
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grades'
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    remarks = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.subject} - "
            f"{self.marks}"
        )


# =========================================================
# ASSIGNMENT
# =========================================================

class Assignment(models.Model):

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    class_group = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='assignments'
    )

    due_date = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title


# =========================================================
# ASSIGNMENT SUBMISSION
# =========================================================

class Submission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True
    )

    file = models.FileField(
        upload_to='assignments/',
        blank=True,
        null=True
    )

    remarks = models.TextField(
        blank=True
    )

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return (
            f"{self.student} - "
            f"{self.assignment}"
        )