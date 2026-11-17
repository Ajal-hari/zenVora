from django.db import models


# ============================================================
# STUDENT
# ============================================================

class Student(models.Model):

    SEMESTER_CHOICES = [
        ('1', '1st Semester'),
        ('2', '2nd Semester'),
        ('3', '3rd Semester'),
        ('4', '4th Semester'),
    ]

    DEPARTMENT_CHOICES = [
        ('MCA', 'MCA'),
        ('MBA', 'MBA'),
        ('BBA', 'BBA'),
    ]

    CLASS_CHOICES = [
        ('A', 'Class A'),
        ('B', 'Class B'),
        ('C', 'Class C'),
        ('D', 'Class D'),
    ]

    name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    password = models.CharField(
        max_length=128
    )

    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES
    )

    semester = models.CharField(
        max_length=1,
        choices=SEMESTER_CHOICES
    )

    class_name = models.CharField(
        max_length=1,
        choices=CLASS_CHOICES
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# ============================================================
# COURSE
# ============================================================

class Course(models.Model):

    name = models.CharField(
        max_length=150
    )

    semester = models.CharField(
        max_length=1,
        choices=Student.SEMESTER_CHOICES
    )

    department = models.CharField(
        max_length=10,
        choices=Student.DEPARTMENT_CHOICES,
        default='MCA'
    )

    def __str__(self):
        return self.name


# ============================================================
# FEEDBACK
# ============================================================

class Feedback(models.Model):

    SENTIMENT_CHOICES = [
        ('Positive', 'Positive'),
        ('Neutral', 'Neutral'),
        ('Negative', 'Negative'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )

    rating = models.IntegerField()

    feedback_text = models.TextField()

    sentiment = models.CharField(
        max_length=20,
        choices=SENTIMENT_CHOICES
    )

    sentiment_score = models.FloatField(
        default=0
    )

    # IMPORTANT:
    # This is the original submission time.
    # The 24-hour edit/delete window is calculated from this field.
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student.name} - {self.course.name}"


# ============================================================
# EMAIL OTP
# ============================================================

class EmailOTP(models.Model):

    email = models.EmailField()

    otp = models.CharField(
        max_length=6
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.email

class RegistrationOTP(models.Model):
    email = models.EmailField(unique=True)
    verifier = models.CharField(max_length=64)
    session_token = models.CharField(max_length=64)
    created_at = models.DateTimeField()
    last_sent_at = models.DateTimeField()
    window_started_at = models.DateTimeField()
    send_count = models.PositiveSmallIntegerField(default=0)
    attempts = models.PositiveSmallIntegerField(default=0)
