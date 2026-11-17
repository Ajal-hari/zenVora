from django.contrib import admin
from .models import Student, Course, Feedback


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'semester', 'class_name', 'created_at')
    search_fields = ('name', 'email')
    list_filter = ('semester', 'class_name')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester')
    search_fields = ('name',)
    list_filter = ('semester',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'student',
        'course',
        'rating',
        'sentiment',
        'sentiment_score',
        'created_at'
    )
    search_fields = (
        'student__name',
        'course__name',
        'feedback_text'
    )
    list_filter = (
        'sentiment',
        'rating',
        'course'
    )