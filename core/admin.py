from django.contrib import admin

from .models import Student, Teacher


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'student_id',
        'get_full_name',
        'get_email',
        'phone',
        'program',
        'semester',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'semester',
        'program',
    )

    search_fields = (
        'student_id',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone',
    )

    ordering = (
        '-created_at',
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):

    list_display = (
        'teacher_id',
        'get_full_name',
        'get_email',
        'phone',
        'department',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'department',
    )

    search_fields = (
        'teacher_id',
        'user__first_name',
        'user__last_name',
        'user__email',
        'phone',
        'department',
    )

    ordering = (
        '-created_at',
    )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    get_full_name.short_description = 'Name'

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'