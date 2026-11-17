from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from django.db.models import Avg
from django.http import HttpResponse
from datetime import timedelta
from datetime import datetime
import random
import re
import csv

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

from .models import Student, EmailOTP, Course, Feedback


# ============================================================
# PDF
# ============================================================

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# ADMIN SETTINGS
# ============================================================

ADMIN_EMAIL = None
ADMIN_PASSWORD = None


# ============================================================
# FEEDBACK EDIT / DELETE SETTINGS
# ============================================================

FEEDBACK_EDIT_DELETE_WINDOW = timedelta(hours=24)


# ============================================================
# HOME
# ============================================================

def home(request):

    return render(
        request,
        'feedback/home.html'
    )


# ============================================================
# LOGIN
# ============================================================

def login_view(request):

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        # ----------------------------------------------------
        # ADMIN LOGIN
        # ----------------------------------------------------

        if (
            email == ADMIN_EMAIL
            and password == ADMIN_PASSWORD
        ):

            request.session.flush()

            request.session[
                'admin_logged_in'
            ] = True

            request.session[
                'admin_email'
            ] = ADMIN_EMAIL

            messages.success(
                request,
                "Administrator login successful!"
            )

            return redirect(
                '/admin-dashboard/'
            )

        # ----------------------------------------------------
        # EMPTY FIELDS
        # ----------------------------------------------------

        if not email or not password:

            messages.error(
                request,
                "Please enter your email and password."
            )

            return render(
                request,
                'feedback/login.html'
            )

        # ----------------------------------------------------
        # STUDENT EMAIL
        # ----------------------------------------------------

        if not email.endswith(
            "@kristujayanti.com"
        ):

            messages.error(
                request,
                "Please use your college email."
            )

            return render(
                request,
                'feedback/login.html'
            )

        # ----------------------------------------------------
        # STUDENT LOGIN
        # ----------------------------------------------------

        try:

            student = Student.objects.get(
                email=email
            )

        except Student.DoesNotExist:

            messages.error(
                request,
                "No account found with this email. Please register first."
            )

            return render(
                request,
                'feedback/login.html'
            )

        if student.password != password:

            messages.error(
                request,
                "Incorrect password."
            )

            return render(
                request,
                'feedback/login.html'
            )

        # ----------------------------------------------------
        # STUDENT SESSION
        # ----------------------------------------------------

        request.session[
            'student_id'
        ] = student.id

        request.session[
            'student_name'
        ] = student.name

        request.session[
            'student_email'
        ] = student.email

        messages.success(
            request,
            f"Login successful! Welcome, {student.name}"
        )

        return redirect(
            '/dashboard/'
        )

    return render(
        request,
        'feedback/login.html'
    )


# ============================================================
# ADMIN LOGIN
# ============================================================

def admin_login(request):

    if request.session.get(
        'admin_logged_in'
    ):

        return redirect(
            '/admin-dashboard/'
        )

    if request.method == "POST":

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        password = request.POST.get(
            "password",
            ""
        )

        if not email or not password:

            messages.error(
                request,
                "Please enter admin email and password."
            )

            return render(
                request,
                'feedback/admin_login.html'
            )

        if (
            email == ADMIN_EMAIL
            and password == ADMIN_PASSWORD
        ):

            request.session.flush()

            request.session[
                'admin_logged_in'
            ] = True

            request.session[
                'admin_email'
            ] = ADMIN_EMAIL

            messages.success(
                request,
                "Admin login successful!"
            )

            return redirect(
                '/admin-dashboard/'
            )

        messages.error(
            request,
            "Invalid administrator credentials."
        )

    return render(
        request,
        'feedback/admin_login.html'
    )


# ============================================================
# ADMIN LOGOUT
# ============================================================

def admin_logout(request):

    request.session.flush()

    messages.success(
        request,
        "Administrator logged out successfully."
    )

    return redirect(
        '/admin-login/'
    )


# ============================================================
# REGISTER
# ============================================================

def register_view(request):

    if request.method == "POST":

        name = request.POST.get(
            "name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip().lower()

        department = request.POST.get(
            "department",
            ""
        )

        semester = request.POST.get(
            "semester",
            ""
        )

        class_name = request.POST.get(
            "class_name",
            ""
        )

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # ----------------------------------------------------
        # EMPTY FIELDS
        # ----------------------------------------------------

        if (
            not name
            or not email
            or not department
            or not semester
            or not class_name
            or not password
            or not confirm_password
        ):

            messages.error(
                request,
                "Please fill all required fields."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # NAME
        # ----------------------------------------------------

        if len(name) < 3:

            messages.error(
                request,
                "Name must contain at least 3 characters."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # EMAIL
        # ----------------------------------------------------

        email_pattern = (
            r'^[A-Za-z0-9._%+-]+@kristujayanti\.com$'
        )

        if not re.match(
            email_pattern,
            email
        ):

            messages.error(
                request,
                "Only college email addresses ending with @kristujayanti.com are allowed."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # DUPLICATE
        # ----------------------------------------------------

        if Student.objects.filter(
            email=email
        ).exists():

            messages.error(
                request,
                "This email is already registered."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        if len(password) < 8:

            messages.error(
                request,
                "Password must contain at least 8 characters."
            )

            return render(
                request,
                'feedback/register.html'
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                'feedback/register.html'
            )

        if not re.search(
            r'[A-Za-z]',
            password
        ):

            messages.error(
                request,
                "Password must contain at least one letter."
            )

            return render(
                request,
                'feedback/register.html'
            )

        if not re.search(
            r'[0-9]',
            password
        ):

            messages.error(
                request,
                "Password must contain at least one number."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # DEPARTMENT
        # ----------------------------------------------------

        if department not in [
            'MCA',
            'MBA',
            'BBA'
        ]:

            messages.error(
                request,
                "Please select a valid department."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # SEMESTER
        # ----------------------------------------------------

        if semester not in [
            '1',
            '2',
            '3',
            '4'
        ]:

            messages.error(
                request,
                "Please select a valid semester."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # CLASS
        # ----------------------------------------------------

        if class_name not in [
            'A',
            'B',
            'C',
            'D'
        ]:

            messages.error(
                request,
                "Please select a valid class."
            )

            return render(
                request,
                'feedback/register.html'
            )

        # ----------------------------------------------------
        # OTP
        # ----------------------------------------------------

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        EmailOTP.objects.filter(
            email=email
        ).delete()

        EmailOTP.objects.create(
            email=email,
            otp=otp
        )

        request.session[
            'registration_data'
        ] = {
            'name': name,
            'email': email,
            'department': department,
            'semester': semester,
            'class_name': class_name,
            'password': password,
        }

        request.session[
            'otp_email'
        ] = email

        send_mail(
            subject="Student Feedback System - OTP",

            message=f"""
Hello {name},

Your OTP for Student Feedback System registration is:

{otp}

This OTP is valid for 5 minutes.

Please do not share this OTP with anyone.

Thank you,

Student Feedback Sentiment Analysis System
""",

            from_email=None,

            recipient_list=[
                email
            ],

            fail_silently=False,
        )

        messages.success(
            request,
            "OTP sent successfully. Please check your email."
        )

        return redirect(
            '/verify-otp/'
        )

    return render(
        request,
        'feedback/register.html'
    )


# ============================================================
# VERIFY OTP
# ============================================================

def verify_otp(request):

    email = request.session.get(
        'otp_email'
    )

    if not email:

        messages.error(
            request,
            "Registration session expired. Please register again."
        )

        return redirect(
            '/register/'
        )

    if request.method == "POST":

        entered_otp = request.POST.get(
            "otp",
            ""
        ).strip()

        try:

            otp_record = EmailOTP.objects.get(
                email=email
            )

        except EmailOTP.DoesNotExist:

            messages.error(
                request,
                "OTP not found. Please request a new OTP."
            )

            return render(
                request,
                'feedback/verify_otp.html',
                {
                    'email': email
                }
            )

        if timezone.now() > (
            otp_record.created_at
            + timedelta(minutes=5)
        ):

            otp_record.delete()

            messages.error(
                request,
                "OTP has expired. Please request a new OTP."
            )

            return render(
                request,
                'feedback/verify_otp.html',
                {
                    'email': email
                }
            )

        if entered_otp != otp_record.otp:

            messages.error(
                request,
                "Incorrect OTP. Please try again."
            )

            return render(
                request,
                'feedback/verify_otp.html',
                {
                    'email': email
                }
            )

        registration_data = request.session.get(
            'registration_data'
        )

        if not registration_data:

            messages.error(
                request,
                "Registration data expired. Please register again."
            )

            return redirect(
                '/register/'
            )

        Student.objects.create(
            name=registration_data['name'],
            email=registration_data['email'],
            password=registration_data['password'],
            department=registration_data['department'],
            semester=registration_data['semester'],
            class_name=registration_data['class_name']
        )

        otp_record.delete()

        request.session.pop(
            'registration_data',
            None
        )

        request.session.pop(
            'otp_email',
            None
        )

        messages.success(
            request,
            "Email verified! Registration successful. Please login."
        )

        return redirect(
            '/login/'
        )

    return render(
        request,
        'feedback/verify_otp.html',
        {
            'email': email
        }
    )


# ============================================================
# RESEND OTP
# ============================================================

def resend_otp(request):

    email = request.session.get(
        'otp_email'
    )

    registration_data = request.session.get(
        'registration_data'
    )

    if not email or not registration_data:

        messages.error(
            request,
            "Registration session expired. Please register again."
        )

        return redirect(
            '/register/'
        )

    otp = str(
        random.randint(
            100000,
            999999
        )
    )

    EmailOTP.objects.filter(
        email=email
    ).delete()

    EmailOTP.objects.create(
        email=email,
        otp=otp
    )

    send_mail(
        subject="Student Feedback System - New OTP",

        message=f"""
Hello {registration_data['name']},

Your new OTP is:

{otp}

This OTP is valid for 5 minutes.

Thank you,

Student Feedback Sentiment Analysis System
""",

        from_email=None,

        recipient_list=[
            email
        ],

        fail_silently=False,
    )

    messages.success(
        request,
        "New OTP sent successfully."
    )

    return redirect(
        '/verify-otp/'
    )


# ============================================================
# SENTIMENT ANALYSIS
# ============================================================

def analyze_sentiment(text, rating=None):
    """Classify student feedback by positive/negative language and context.

    Mixed positive and negative feedback (e.g. 'good but little bit lag')
    is Neutral. Stars are used only when the text has no sentiment cues.
    """
    text = (text or "").strip().lower()

    # Normalize common contractions so negation is recognised.
    contractions = {
        "isn't": "is not", "aren't": "are not",
        "wasn't": "was not", "weren't": "were not",
        "doesn't": "does not", "don't": "do not",
        "didn't": "did not", "can't": "can not",
        "cannot": "can not", "couldn't": "could not",
        "won't": "will not", "wouldn't": "would not",
        "shouldn't": "should not", "hasn't": "has not",
    }
    for short, expanded in contractions.items():
        text = re.sub(r"\b" + re.escape(short) + r"\b", expanded, text)

    words = re.findall(r"[a-z]+", text)

    # A common classroom sarcasm/complaint is that a lecture is so
    # unengaging that the student can sleep through it.  Simple
    # dictionaries would mark "classes are going well, so I can easily
    # sleep during class" as Positive because they only see "well".
    # Handle these explicit classroom-boredom descriptions first.
    # This is a targeted rule, NOT a general sarcasm detector.
    classroom_boredom_patterns = [
        r"\b(?:i|we)\s+(?:can|could|often|always|usually|sometimes|easily|just)\s+(?:[a-z]+\s+){0,3}(?:sleep|nap|doze|fall asleep)\b.{0,55}\b(?:during|in|through)\s+(?:the\s+|my\s+|our\s+)?(?:class|classes|lecture|lectures|lesson|lessons|session|sessions)\b",
        r"\b(?:i|we)\s+(?:sleep|slept|sleeping|fell asleep|dozed off)\b.{0,55}\b(?:during|in|through)\s+(?:the\s+|my\s+|our\s+)?(?:class|classes|lecture|lectures|lesson|lessons|session|sessions)\b",
        r"\b(?:fall|fell)\s+asleep\b.{0,55}\b(?:during|in|through)\s+(?:the\s+|my\s+|our\s+)?(?:class|classes|lecture|lectures|lesson|lessons|session|sessions)\b",
        r"\b(?:class|classes|lecture|lectures|lesson|lessons|session|sessions|teaching)\b.{0,55}\b(?:makes|made|making)\s+(?:me|us)\s+(?:feel\s+)?(?:sleepy|drowsy|bored)\b",
        r"\b(?:class|classes|lecture|lectures|lesson|lessons|session|sessions|teaching)\b.{0,55}\b(?:puts|put)\s+(?:me|us)\s+to\s+sleep\b",
        r"\b(?:i|we)\s+(?:feel|felt|am|was|were|get|got)\s+(?:very\s+|so\s+|really\s+)?(?:sleepy|drowsy|bored)\b.{0,55}\b(?:during|in)\s+(?:the\s+|my\s+|our\s+)?(?:class|classes|lecture|lectures|lesson|lessons|session|sessions)\b",
    ]
    if any(re.search(pattern, text) for pattern in classroom_boredom_patterns):
        return ("Negative", -0.8)

    # Longer phrases are matched before individual words to avoid
    # counting 'good' inside 'not good', or 'lag' inside 'no lag'.
    positive_phrases = {
        "good", "great", "excellent", "amazing", "helpful", "best",
        "love", "loved", "like", "liked", "enjoy", "enjoyed",
        "interesting", "clear", "perfect", "fantastic", "awesome",
        "effective", "useful", "supportive", "satisfied", "happy",
        "wonderful", "nice", "well", "better", "improved",
        "understand", "understood", "easy", "engaging",
        "knowledgeable", "informative", "smooth", "fast", "excellent work",
        "well explained", "easy to understand", "works well",
        "no issues", "no issue", "no problems", "no problem",
        "no lag", "lag free", "not bad", "not slow",
        "not difficult", "not boring",
    }

    negative_phrases = {
        "bad", "poor", "worst", "terrible", "awful", "hate", "hated",
        "boring", "confusing", "confused", "difficult", "hard",
        "insufficient", "lack", "lacking", "problem", "problems",
        "issue", "issues", "weak", "slow", "unhelpful", "unsatisfied",
        "unhappy", "disappointed", "disappointing", "unclear",
        "useless", "dissatisfied", "inadequate", "bug", "bugs",
        "error", "errors", "crash", "crashes", "crashed",
        "delay", "delays", "lag", "lags", "laggy", "lagging",
        "unresponsive", "improve", "not enough", "not sufficient",
        "not clear", "not useful", "not good", "not helpful",
        "not satisfied", "not interesting", "needs improvement",
        "need improvement", "needs to improve", "could be better",
        "too slow", "little bit lag", "bit lag", "too much lag",
        "hard to understand", "does not work", "not working",
    }

    phrase_polarities = (
        [(tuple(phrase.split()), 1) for phrase in positive_phrases]
        + [(tuple(phrase.split()), -1) for phrase in negative_phrases]
    )
    # Make ordering deterministic within a phrase length.
    phrase_polarities.sort(key=lambda item: (-len(item[0]), item[0]))

    positive_count = 0
    negative_count = 0
    index = 0
    while index < len(words):
        match = None
        for phrase, polarity in phrase_polarities:
            length = len(phrase)
            if tuple(words[index:index + length]) == phrase:
                match = (length, polarity)
                break

        if match is None:
            index += 1
            continue

        length, polarity = match

        # Handle 'not good', 'not very helpful', 'not bad', etc.
        # Explicit multiword negated phrases above already have polarity.
        if length == 1:
            context = words[max(0, index - 3):index]
            for position, token in enumerate(context):
                if token in {"but", "however", "though", "although", "yet", "and", "or", "so"}:
                    context = context[position + 1:]
            if any(token in context for token in ("not", "never", "no")):
                # 'not only good' is positive, not negated.
                if not ("not" in context and "only" in context):
                    polarity = -polarity

        if polarity > 0:
            positive_count += 1
        else:
            negative_count += 1
        index += length

    has_contrast = any(
        word in {"but", "however", "although", "though", "yet"}
        for word in words
    )

    # Opinions containing both praise and criticism are mixed/Neutral,
    # regardless of a high or low star rating.
    if positive_count and negative_count:
        if has_contrast or abs(positive_count - negative_count) <= 1:
            return ("Neutral", 0.0)
        if positive_count > negative_count:
            return ("Positive", round(min(1.0, positive_count / 5), 2))
        return ("Negative", round(max(-1.0, -negative_count / 5), 2))

    if positive_count:
        return ("Positive", round(min(1.0, positive_count / 5), 2))
    if negative_count:
        return ("Negative", round(max(-1.0, -negative_count / 5), 2))

    # If written feedback is emotionally neutral, use rating as fallback.
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return ("Neutral", 0.0)

    if rating >= 4:
        return ("Positive", 0.8)
    if rating <= 2:
        return ("Negative", -0.8)
    return ("Neutral", 0.0)


# ============================================================
# STUDENT DASHBOARD
# ============================================================

def dashboard(request):

    student_id = request.session.get(
        'student_id'
    )

    if not student_id:

        messages.error(
            request,
            "Please login first."
        )

        return redirect(
            '/login/'
        )

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        request.session.flush()

        messages.error(
            request,
            "Student account not found."
        )

        return redirect(
            '/login/'
        )

    feedbacks = Feedback.objects.filter(
        student=student
    ).select_related(
        'course'
    ).order_by(
        '-created_at'
    )

    now = timezone.now()

    for feedback in feedbacks:

        deadline = (
            feedback.created_at
            + FEEDBACK_EDIT_DELETE_WINDOW
        )

        feedback.can_modify = now <= deadline

        feedback.edit_delete_deadline = deadline

    total_feedback = feedbacks.count()

    positive_count = feedbacks.filter(
        sentiment='Positive'
    ).count()

    neutral_count = feedbacks.filter(
        sentiment='Neutral'
    ).count()

    negative_count = feedbacks.filter(
        sentiment='Negative'
    ).count()

    ratings = list(
        feedbacks.values_list(
            'rating',
            flat=True
        )
    )

    if ratings:

        average_rating = round(
            sum(ratings) / len(ratings),
            1
        )

    else:

        average_rating = 0

    if total_feedback > 0:

        positive_percentage = round(
            positive_count
            / total_feedback
            * 100
        )

        neutral_percentage = round(
            neutral_count
            / total_feedback
            * 100
        )

        negative_percentage = round(
            negative_count
            / total_feedback
            * 100
        )

    else:

        positive_percentage = 0
        neutral_percentage = 0
        negative_percentage = 0

    context = {

        'student': student,
        'feedbacks': feedbacks,
        'total_feedback': total_feedback,
        'positive_count': positive_count,
        'neutral_count': neutral_count,
        'negative_count': negative_count,
        'positive_percentage': positive_percentage,
        'neutral_percentage': neutral_percentage,
        'negative_percentage': negative_percentage,
        'average_rating': average_rating,
    }

    return render(
        request,
        'feedback/dashboard.html',
        context
    )


# ============================================================
# FEEDBACK
# ============================================================

def feedback_view(request):

    student_id = request.session.get(
        'student_id'
    )

    if not student_id:

        messages.error(
            request,
            "Please login first."
        )

        return redirect(
            '/login/'
        )

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        request.session.flush()

        return redirect(
            '/login/'
        )

    # --------------------------------------------------------
    # SUBMIT NEW FEEDBACK
    # --------------------------------------------------------

    if request.method == "POST":

        course_id = request.POST.get(
            "course"
        )

        rating = request.POST.get(
            "rating"
        )

        feedback_text = request.POST.get(
            "feedback_text",
            ""
        ).strip()

        if not course_id:

            messages.error(
                request,
                "Please select a course."
            )

            return redirect(
                '/feedback/'
            )

        try:

            rating = int(rating)

        except (
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "Please select a valid rating."
            )

            return redirect(
                '/feedback/'
            )

        if rating < 1 or rating > 5:

            messages.error(
                request,
                "Rating must be between 1 and 5."
            )

            return redirect(
                '/feedback/'
            )

        if len(feedback_text) < 5:

            messages.error(
                request,
                "Feedback must contain at least 5 characters."
            )

            return redirect(
                '/feedback/'
            )

        try:

            course = Course.objects.get(
                id=course_id
            )

        except Course.DoesNotExist:

            messages.error(
                request,
                "Selected course does not exist."
            )

            return redirect(
                '/feedback/'
            )

        if (
            course.department
            != student.department
            or course.semester
            != student.semester
        ):

            messages.error(
                request,
                "Invalid course selection."
            )

            return redirect(
                '/feedback/'
            )

        sentiment, sentiment_score = analyze_sentiment(
            feedback_text,
            rating
        )

        Feedback.objects.create(

            student=student,

            course=course,

            rating=rating,

            feedback_text=feedback_text,

            sentiment=sentiment,

            sentiment_score=sentiment_score
        )

        messages.success(
            request,
            f"Feedback submitted successfully! Sentiment detected: {sentiment}."
        )

        return redirect(
            '/dashboard/'
        )

    courses = Course.objects.filter(
        department=student.department,
        semester=student.semester
    ).order_by(
        'name'
    )

    my_feedbacks = Feedback.objects.filter(
        student=student
    ).select_related(
        'course'
    ).order_by(
        '-created_at'
    )

    now = timezone.now()

    for feedback in my_feedbacks:

        feedback.edit_delete_deadline = (
            feedback.created_at
            + FEEDBACK_EDIT_DELETE_WINDOW
        )

        feedback.can_modify = (
            now <= feedback.edit_delete_deadline
        )

    return render(
        request,
        'feedback/feedback.html',
        {
            'student': student,
            'courses': courses,
            'my_feedbacks': my_feedbacks,
        }
    )


# ============================================================
# EDIT FEEDBACK
# ============================================================

def edit_feedback(request, feedback_id):

    student_id = request.session.get(
        'student_id'
    )

    if not student_id:

        messages.error(
            request,
            "Please login first."
        )

        return redirect(
            '/login/'
        )

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        request.session.flush()

        messages.error(
            request,
            "Student account not found."
        )

        return redirect(
            '/login/'
        )

    feedback = get_object_or_404(
        Feedback,
        id=feedback_id,
        student=student
    )

    deadline = (
        feedback.created_at
        + FEEDBACK_EDIT_DELETE_WINDOW
    )

    if timezone.now() > deadline:

        messages.error(
            request,
            "The 24-hour editing period has expired. This feedback can no longer be edited."
        )

        return redirect(
            '/feedback/'
        )

    if request.method == "POST":

        rating = request.POST.get(
            "rating"
        )

        feedback_text = request.POST.get(
            "feedback_text",
            ""
        ).strip()

        try:

            rating = int(rating)

        except (
            ValueError,
            TypeError
        ):

            messages.error(
                request,
                "Please select a valid rating."
            )

            return render(
                request,
                'feedback/edit_feedback.html',
                {
                    'student': student,
                    'feedback': feedback,
                    'deadline': deadline,
                }
            )

        if rating < 1 or rating > 5:

            messages.error(
                request,
                "Rating must be between 1 and 5."
            )

            return render(
                request,
                'feedback/edit_feedback.html',
                {
                    'student': student,
                    'feedback': feedback,
                    'deadline': deadline,
                }
            )

        if len(feedback_text) < 5:

            messages.error(
                request,
                "Feedback must contain at least 5 characters."
            )

            return render(
                request,
                'feedback/edit_feedback.html',
                {
                    'student': student,
                    'feedback': feedback,
                    'deadline': deadline,
                }
            )

        if timezone.now() > deadline:

            messages.error(
                request,
                "The 24-hour editing period has expired. This feedback can no longer be edited."
            )

            return redirect(
                '/feedback/'
            )

        sentiment, sentiment_score = analyze_sentiment(
            feedback_text,
            rating
        )

        feedback.rating = rating

        feedback.feedback_text = feedback_text

        feedback.sentiment = sentiment

        feedback.sentiment_score = sentiment_score

        feedback.save(
            update_fields=[
                'rating',
                'feedback_text',
                'sentiment',
                'sentiment_score'
            ]
        )

        messages.success(
            request,
            "Your feedback has been updated successfully."
        )

        return redirect(
            '/feedback/'
        )

    return render(
        request,
        'feedback/edit_feedback.html',
        {
            'student': student,
            'feedback': feedback,
            'deadline': deadline,
        }
    )


# ============================================================
# DELETE FEEDBACK
# ============================================================

def delete_feedback(request, feedback_id):

    student_id = request.session.get(
        'student_id'
    )

    if not student_id:

        messages.error(
            request,
            "Please login first."
        )

        return redirect(
            '/login/'
        )

    try:

        student = Student.objects.get(
            id=student_id
        )

    except Student.DoesNotExist:

        request.session.flush()

        messages.error(
            request,
            "Student account not found."
        )

        return redirect(
            '/login/'
        )

    feedback = get_object_or_404(
        Feedback,
        id=feedback_id,
        student=student
    )

    if request.method != "POST":

        messages.error(
            request,
            "Invalid delete request."
        )

        return redirect(
            '/feedback/'
        )

    deadline = (
        feedback.created_at
        + FEEDBACK_EDIT_DELETE_WINDOW
    )

    if timezone.now() > deadline:

        messages.error(
            request,
            "The 24-hour deletion period has expired. This feedback can no longer be deleted."
        )

        return redirect(
            '/feedback/'
        )

    course_name = feedback.course.name

    feedback.delete()

    messages.success(
        request,
        f"Your feedback for {course_name} has been deleted successfully."
    )

    return redirect(
        '/feedback/'
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard(request):

    # --------------------------------------------------------
    # ADMIN LOGIN CHECK
    # --------------------------------------------------------

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    # --------------------------------------------------------
    # ALL COURSES
    # --------------------------------------------------------

    courses = Course.objects.all().order_by(
        'semester',
        'department',
        'name'
    )

    # --------------------------------------------------------
    # SELECTED COURSE
    # --------------------------------------------------------

    selected_course_id = request.GET.get(
        'course_id'
    )

    selected_course = None

    # --------------------------------------------------------
    # DEFAULT:
    # NO FEEDBACK UNTIL COURSE IS SELECTED
    # --------------------------------------------------------

    if selected_course_id:

        selected_course = get_object_or_404(
            Course,
            id=selected_course_id
        )

        feedbacks = Feedback.objects.filter(
            course=selected_course
        ).select_related(
            'student',
            'course'
        ).order_by(
            '-created_at'
        )

    else:

        feedbacks = Feedback.objects.none()

    # --------------------------------------------------------
    # COURSE-SPECIFIC ANALYTICS
    # --------------------------------------------------------

    total_feedback = feedbacks.count()

    positive_count = feedbacks.filter(
        sentiment='Positive'
    ).count()

    neutral_count = feedbacks.filter(
        sentiment='Neutral'
    ).count()

    negative_count = feedbacks.filter(
        sentiment='Negative'
    ).count()

    # --------------------------------------------------------
    # GLOBAL COUNTS
    # --------------------------------------------------------

    total_students = Student.objects.count()

    total_courses = Course.objects.count()

    # --------------------------------------------------------
    # COURSE-SPECIFIC AVERAGE RATING
    # --------------------------------------------------------

    average_rating = feedbacks.aggregate(
        Avg('rating')
    )['rating__avg']

    if average_rating is None:

        average_rating = 0

    else:

        average_rating = round(
            average_rating,
            2
        )

    # --------------------------------------------------------
    # COURSE-SPECIFIC SENTIMENT PERCENTAGES
    # --------------------------------------------------------

    if total_feedback > 0:

        positive_percentage = round(
            positive_count
            / total_feedback
            * 100
        )

        neutral_percentage = round(
            neutral_count
            / total_feedback
            * 100
        )

        negative_percentage = round(
            negative_count
            / total_feedback
            * 100
        )

    else:

        positive_percentage = 0

        neutral_percentage = 0

        negative_percentage = 0

    # --------------------------------------------------------
    # STUDENTS
    # --------------------------------------------------------

    students = Student.objects.all().order_by(
        'name'
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {

        'feedbacks': feedbacks,

        'students': students,

        'courses': courses,

        'selected_course': selected_course,

        'selected_course_id': selected_course_id,

        'total_feedback': total_feedback,

        'positive_count': positive_count,

        'neutral_count': neutral_count,

        'negative_count': negative_count,

        'total_students': total_students,

        'total_courses': total_courses,

        'average_rating': average_rating,

        'positive_percentage': positive_percentage,

        'neutral_percentage': neutral_percentage,

        'negative_percentage': negative_percentage,

        'admin_email': ADMIN_EMAIL,
    }

    return render(
        request,
        'feedback/admin_dashboard.html',
        context
    )


# ============================================================
# ADMIN ADD COURSE
# ============================================================

def admin_add_course(request):

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    if request.method == "POST":

        name = request.POST.get(
            'name',
            ''
        ).strip()

        department = request.POST.get(
            'department',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        if not name or not department or not semester:

            messages.error(
                request,
                "Please fill all course fields."
            )

            return redirect(
                '/admin-dashboard/'
            )

        if department not in [
            'MCA',
            'MBA',
            'BBA'
        ]:

            messages.error(
                request,
                "Invalid department selected."
            )

            return redirect(
                '/admin-dashboard/'
            )

        if semester not in [
            '1',
            '2',
            '3',
            '4'
        ]:

            messages.error(
                request,
                "Invalid semester selected."
            )

            return redirect(
                '/admin-dashboard/'
            )

        Course.objects.create(
            name=name,
            department=department,
            semester=semester
        )

        messages.success(
            request,
            f"Course '{name}' added successfully."
        )

        return redirect(
            '/admin-dashboard/#courses'
        )

    return redirect(
        '/admin-dashboard/'
    )


# ============================================================
# ADMIN UPDATE COURSE
# ============================================================

def admin_update_course(
    request,
    course_id
):

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    course = get_object_or_404(
        Course,
        id=course_id
    )

    if request.method == "POST":

        name = request.POST.get(
            'name',
            ''
        ).strip()

        department = request.POST.get(
            'department',
            ''
        ).strip()

        semester = request.POST.get(
            'semester',
            ''
        ).strip()

        if not name or not department or not semester:

            messages.error(
                request,
                "All course fields are required."
            )

            return redirect(
                '/admin-dashboard/#courses'
            )

        if department not in [
            'MCA',
            'MBA',
            'BBA'
        ]:

            messages.error(
                request,
                "Invalid department selected."
            )

            return redirect(
                '/admin-dashboard/#courses'
            )

        if semester not in [
            '1',
            '2',
            '3',
            '4'
        ]:

            messages.error(
                request,
                "Invalid semester selected."
            )

            return redirect(
                '/admin-dashboard/#courses'
            )

        course.name = name

        course.department = department

        course.semester = semester

        course.save()

        messages.success(
            request,
            f"Course '{name}' updated successfully."
        )

    return redirect(
        '/admin-dashboard/#courses'
    )


# ============================================================
# ADMIN DELETE COURSE
# ============================================================

def admin_delete_course(
    request,
    course_id
):

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    course = get_object_or_404(
        Course,
        id=course_id
    )

    if request.method == "POST":

        course_name = course.name

        course.delete()

        messages.success(
            request,
            f"Course '{course_name}' deleted successfully."
        )

    return redirect(
        '/admin-dashboard/#courses'
    )


# ============================================================
# DOWNLOAD COURSE FEEDBACK - CSV
# ============================================================

def download_course_csv(
    request,
    course_id
):

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    course = get_object_or_404(
        Course,
        id=course_id
    )

    feedbacks = Feedback.objects.filter(
        course=course
    ).select_related(
        'student'
    ).order_by(
        '-created_at'
    )

    response = HttpResponse(
        content_type='text/csv'
    )

    filename = (
        f"{course.name.replace(' ', '_')}_feedback.csv"
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename="{filename}"'

    writer = csv.writer(
        response
    )

    writer.writerow([
        'STUDENT FEEDBACK ANALYTICAL REPORT'
    ])

    writer.writerow([])

    writer.writerow([
        'Course',
        course.name
    ])

    writer.writerow([
        'Department',
        course.get_department_display()
    ])

    writer.writerow([
        'Semester',
        course.get_semester_display()
    ])

    writer.writerow([])

    total_feedback = feedbacks.count()

    positive_count = feedbacks.filter(
        sentiment='Positive'
    ).count()

    neutral_count = feedbacks.filter(
        sentiment='Neutral'
    ).count()

    negative_count = feedbacks.filter(
        sentiment='Negative'
    ).count()

    average_rating = feedbacks.aggregate(
        Avg('rating')
    )['rating__avg']

    if average_rating is None:

        average_rating = 0

    else:

        average_rating = round(
            average_rating,
            2
        )

    if total_feedback > 0:

        positive_percentage = round(
            positive_count
            / total_feedback
            * 100,
            2
        )

        neutral_percentage = round(
            neutral_count
            / total_feedback
            * 100,
            2
        )

        negative_percentage = round(
            negative_count
            / total_feedback
            * 100,
            2
        )

    else:

        positive_percentage = 0
        neutral_percentage = 0
        negative_percentage = 0

    writer.writerow([
        'Total Feedback',
        total_feedback
    ])

    writer.writerow([
        'Average Rating',
        average_rating
    ])

    writer.writerow([
        'Positive',
        positive_count
    ])

    writer.writerow([
        'Positive Percentage',
        f'{positive_percentage}%'
    ])

    writer.writerow([
        'Neutral',
        neutral_count
    ])

    writer.writerow([
        'Neutral Percentage',
        f'{neutral_percentage}%'
    ])

    writer.writerow([
        'Negative',
        negative_count
    ])

    writer.writerow([
        'Negative Percentage',
        f'{negative_percentage}%'
    ])

    writer.writerow([])

    writer.writerow([
        'Student Name',
        'Student Email',
        'Rating',
        'Feedback',
        'Sentiment',
        'Sentiment Score',
        'Date'
    ])

    for feedback in feedbacks:

        writer.writerow([
            feedback.student.name,
            feedback.student.email,
            feedback.rating,
            feedback.feedback_text,
            feedback.sentiment,
            feedback.sentiment_score,
            feedback.created_at.strftime(
                '%d-%m-%Y %I:%M %p'
            )
        ])

    return response


# ============================================================
# DOWNLOAD COURSE ANALYTICAL REPORT - PDF
# ============================================================

def download_course_pdf(
    request,
    course_id
):

    if not request.session.get(
        'admin_logged_in'
    ):

        messages.error(
            request,
            "Administrator login required."
        )

        return redirect(
            '/admin-login/'
        )

    course = get_object_or_404(
        Course,
        id=course_id
    )

    feedbacks = Feedback.objects.filter(
        course=course
    ).select_related(
        'student'
    ).order_by(
        '-created_at'
    )

    total_feedback = feedbacks.count()

    positive_count = feedbacks.filter(
        sentiment='Positive'
    ).count()

    neutral_count = feedbacks.filter(
        sentiment='Neutral'
    ).count()

    negative_count = feedbacks.filter(
        sentiment='Negative'
    ).count()

    average_rating = feedbacks.aggregate(
        Avg('rating')
    )['rating__avg']

    if average_rating is None:

        average_rating = 0

    else:

        average_rating = round(
            average_rating,
            2
        )

    if total_feedback > 0:

        positive_percentage = round(
            positive_count
            / total_feedback
            * 100,
            2
        )

        neutral_percentage = round(
            neutral_count
            / total_feedback
            * 100,
            2
        )

        negative_percentage = round(
            negative_count
            / total_feedback
            * 100,
            2
        )

    else:

        positive_percentage = 0
        neutral_percentage = 0
        negative_percentage = 0

    response = HttpResponse(
        content_type='application/pdf'
    )

    filename = (
        f"{course.name.replace(' ', '_')}_analytical_report.pdf"
    )

    response[
        'Content-Disposition'
    ] = f'attachment; filename="{filename}"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        'ReportHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=12,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        'ReportNormal',
        parent=styles['BodyText'],
        fontSize=9,
        leading=12
    )

    small_style = ParagraphStyle(
        'SmallText',
        parent=styles['BodyText'],
        fontSize=7,
        leading=9
    )

    story = []

    story.append(
        Paragraph(
            "Student Feedback Sentiment Analysis",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Course-wise Analytical Report",
            heading_style
        )
    )

    story.append(
        Spacer(
            1,
            10
        )
    )

    course_data = [

        [
            Paragraph(
                '<b>Course</b>',
                normal_style
            ),
            Paragraph(
                course.name,
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Department</b>',
                normal_style
            ),
            Paragraph(
                course.get_department_display(),
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Semester</b>',
                normal_style
            ),
            Paragraph(
                course.get_semester_display(),
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Generated On</b>',
                normal_style
            ),
            Paragraph(
                datetime.now().strftime(
                    '%d-%m-%Y %I:%M %p'
                ),
                normal_style
            )
        ]
    ]

    course_table = Table(
        course_data,
        colWidths=[
            130,
            350
        ]
    )

    course_table.setStyle(
        TableStyle([

            (
                'GRID',
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                'BACKGROUND',
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                'VALIGN',
                (0, 0),
                (-1, -1),
                'TOP'
            ),

            (
                'PADDING',
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(
        course_table
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    story.append(
        Paragraph(
            "Analytical Summary",
            heading_style
        )
    )

    analytics_data = [

        [
            Paragraph(
                '<b>Total Feedback</b>',
                normal_style
            ),
            Paragraph(
                str(total_feedback),
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Average Rating</b>',
                normal_style
            ),
            Paragraph(
                f'{average_rating} / 5',
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Positive Feedback</b>',
                normal_style
            ),
            Paragraph(
                f'{positive_count} ({positive_percentage}%)',
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Neutral Feedback</b>',
                normal_style
            ),
            Paragraph(
                f'{neutral_count} ({neutral_percentage}%)',
                normal_style
            )
        ],

        [
            Paragraph(
                '<b>Negative Feedback</b>',
                normal_style
            ),
            Paragraph(
                f'{negative_count} ({negative_percentage}%)',
                normal_style
            )
        ]
    ]

    analytics_table = Table(
        analytics_data,
        colWidths=[
            180,
            300
        ]
    )

    analytics_table.setStyle(
        TableStyle([

            (
                'GRID',
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                'BACKGROUND',
                (0, 0),
                (0, -1),
                colors.lightgrey
            ),

            (
                'PADDING',
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(
        analytics_table
    )

    story.append(
        Spacer(
            1,
            20
        )
    )

    story.append(
        Paragraph(
            "Sentiment Distribution",
            heading_style
        )
    )

    sentiment_data = [

        [
            Paragraph(
                '<b>Sentiment</b>',
                normal_style
            ),

            Paragraph(
                '<b>Count</b>',
                normal_style
            ),

            Paragraph(
                '<b>Percentage</b>',
                normal_style
            )
        ],

        [
            'Positive',
            str(positive_count),
            f'{positive_percentage}%'
        ],

        [
            'Neutral',
            str(neutral_count),
            f'{neutral_percentage}%'
        ],

        [
            'Negative',
            str(negative_count),
            f'{negative_percentage}%'
        ]
    ]

    sentiment_table = Table(
        sentiment_data,
        colWidths=[
            180,
            120,
            180
        ]
    )

    sentiment_table.setStyle(
        TableStyle([

            (
                'GRID',
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),

            (
                'BACKGROUND',
                (0, 0),
                (-1, 0),
                colors.lightgrey
            ),

            (
                'ALIGN',
                (1, 1),
                (-1, -1),
                'CENTER'
            ),

            (
                'PADDING',
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(
        sentiment_table
    )

    story.append(
        Spacer(
            1,
            25
        )
    )

    story.append(
        Paragraph(
            "Student Feedback Details",
            heading_style
        )
    )

    if feedbacks.exists():

        feedback_data = [

            [
                Paragraph(
                    '<b>Student</b>',
                    small_style
                ),

                Paragraph(
                    '<b>Rating</b>',
                    small_style
                ),

                Paragraph(
                    '<b>Feedback</b>',
                    small_style
                ),

                Paragraph(
                    '<b>Sentiment</b>',
                    small_style
                ),

                Paragraph(
                    '<b>Score</b>',
                    small_style
                ),

                Paragraph(
                    '<b>Date</b>',
                    small_style
                )
            ]
        ]

        for feedback in feedbacks:

            feedback_data.append([

                Paragraph(
                    f"{feedback.student.name}<br/>{feedback.student.email}",
                    small_style
                ),

                Paragraph(
                    str(feedback.rating),
                    small_style
                ),

                Paragraph(
                    feedback.feedback_text,
                    small_style
                ),

                Paragraph(
                    feedback.sentiment,
                    small_style
                ),

                Paragraph(
                    str(feedback.sentiment_score),
                    small_style
                ),

                Paragraph(
                    feedback.created_at.strftime(
                        '%d-%m-%Y'
                    ),
                    small_style
                )
            ])

        feedback_table = Table(
            feedback_data,

            colWidths=[
                105,
                45,
                190,
                70,
                45,
                65
            ],

            repeatRows=1
        )

        feedback_table.setStyle(
            TableStyle([

                (
                    'GRID',
                    (0, 0),
                    (-1, -1),
                    0.4,
                    colors.grey
                ),

                (
                    'BACKGROUND',
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    'VALIGN',
                    (0, 0),
                    (-1, -1),
                    'TOP'
                ),

                (
                    'PADDING',
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        story.append(
            feedback_table
        )

    else:

        story.append(
            Paragraph(
                "No feedback has been submitted for this course.",
                normal_style
            )
        )

    story.append(
        Spacer(
            1,
            20
        )
    )

    story.append(
        Paragraph(
            "Generated by Student Feedback Sentiment Analysis System",
            small_style
        )
    )

    doc.build(
        story
    )

    return response


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    request.session.flush()

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect(
        '/login/'
    )

# ============================================================
# ADMIN EDIT FEEDBACK
# ============================================================

def admin_edit_feedback(request, feedback_id):

    if not request.session.get('admin_logged_in'):
        messages.error(request, "Administrator login required.")
        return redirect('/admin-login/')

    feedback = get_object_or_404(Feedback, id=feedback_id)
    course_id = feedback.course.id

    if request.method == "POST":

        rating = request.POST.get('rating', '')
        feedback_text = request.POST.get('feedback_text', '').strip()

        try:
            rating = int(rating)
        except (ValueError, TypeError):
            messages.error(request, "Invalid rating.")
            return redirect('/admin-dashboard/?course_id={}'.format(course_id))

        if rating < 1 or rating > 5:
            messages.error(request, "Rating must be between 1 and 5.")
            return redirect('/admin-dashboard/?course_id={}'.format(course_id))

        if len(feedback_text) < 5:
            messages.error(request, "Feedback must contain at least 5 characters.")
            return redirect('/admin-dashboard/?course_id={}'.format(course_id))

        sentiment, sentiment_score = analyze_sentiment(
            feedback_text,
            rating
        )

        feedback.rating = rating
        feedback.feedback_text = feedback_text
        feedback.sentiment = sentiment
        feedback.sentiment_score = sentiment_score

        # IMPORTANT:
        # Do not change feedback.created_at.
        # It remains the original student submission time.
        feedback.save(
            update_fields=[
                'rating',
                'feedback_text',
                'sentiment',
                'sentiment_score'
            ]
        )

        messages.success(
            request,
            "Feedback updated successfully by administrator."
        )

    return redirect(
        '/admin-dashboard/?course_id={}'.format(course_id)
    )


# ============================================================
# ADMIN DELETE FEEDBACK
# ============================================================

def admin_delete_feedback(request, feedback_id):

    if not request.session.get('admin_logged_in'):
        messages.error(request, "Administrator login required.")
        return redirect('/admin-login/')

    feedback = get_object_or_404(Feedback, id=feedback_id)
    course_id = feedback.course.id

    if request.method != "POST":
        messages.error(request, "Invalid delete request.")
        return redirect(
            '/admin-dashboard/?course_id={}'.format(course_id)
        )

    course_name = feedback.course.name
    feedback.delete()

    messages.success(
        request,
        "Feedback for {} deleted successfully by administrator.".format(
            course_name
        )
    )

    return redirect(
        '/admin-dashboard/?course_id={}'.format(course_id)
    )


# ============================================================
# DOWNLOAD COURSE FEEDBACK - EXCEL
# ============================================================

def download_course_excel(request, course_id):

    if not request.session.get('admin_logged_in'):
        messages.error(request, "Administrator login required.")
        return redirect('/admin-login/')

    course = get_object_or_404(Course, id=course_id)

    feedbacks = Feedback.objects.filter(
        course=course
    ).select_related(
        'student'
    ).order_by(
        '-created_at'
    )

    total_feedback = feedbacks.count()

    positive_count = feedbacks.filter(
        sentiment='Positive'
    ).count()

    neutral_count = feedbacks.filter(
        sentiment='Neutral'
    ).count()

    negative_count = feedbacks.filter(
        sentiment='Negative'
    ).count()

    average_rating = feedbacks.aggregate(
        Avg('rating')
    )['rating__avg']

    if average_rating is None:
        average_rating = 0
    else:
        average_rating = round(average_rating, 2)

    if total_feedback > 0:
        positive_percentage = round(
            positive_count / total_feedback * 100,
            2
        )
        neutral_percentage = round(
            neutral_count / total_feedback * 100,
            2
        )
        negative_percentage = round(
            negative_count / total_feedback * 100,
            2
        )
    else:
        positive_percentage = 0
        neutral_percentage = 0
        negative_percentage = 0

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Feedback Report"

    # --------------------------------------------------------
    # STYLES
    # --------------------------------------------------------

    title_font = Font(
        bold=True,
        size=16
    )

    header_font = Font(
        bold=True,
        color="FFFFFF"
    )

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F2937"
    )

    summary_fill = PatternFill(
        fill_type="solid",
        fgColor="E5E7EB"
    )

    center_alignment = Alignment(
        horizontal="center",
        vertical="center",
        wrap_text=True
    )

    wrap_alignment = Alignment(
        vertical="top",
        wrap_text=True
    )

    # --------------------------------------------------------
    # REPORT TITLE
    # --------------------------------------------------------

    worksheet.merge_cells('A1:H1')
    worksheet['A1'] = 'Student Feedback Sentiment Analysis Report'
    worksheet['A1'].font = title_font
    worksheet['A1'].alignment = center_alignment

    worksheet['A2'] = 'Course'
    worksheet['B2'] = course.name
    worksheet['A3'] = 'Department'
    worksheet['B3'] = course.get_department_display()
    worksheet['A4'] = 'Semester'
    worksheet['B4'] = course.get_semester_display()
    worksheet['A5'] = 'Generated On'
    worksheet['B5'] = datetime.now().strftime('%d-%m-%Y %I:%M %p')

    for row in range(2, 6):
        worksheet['A{}'.format(row)].font = Font(bold=True)
        worksheet['A{}'.format(row)].fill = summary_fill

    # --------------------------------------------------------
    # ANALYTICAL SUMMARY
    # --------------------------------------------------------

    worksheet['D2'] = 'Total Feedback'
    worksheet['E2'] = total_feedback
    worksheet['D3'] = 'Average Rating'
    worksheet['E3'] = average_rating
    worksheet['D4'] = 'Positive'
    worksheet['E4'] = '{} ({}%)'.format(
        positive_count,
        positive_percentage
    )
    worksheet['D5'] = 'Neutral'
    worksheet['E5'] = '{} ({}%)'.format(
        neutral_count,
        neutral_percentage
    )
    worksheet['D6'] = 'Negative'
    worksheet['E6'] = '{} ({}%)'.format(
        negative_count,
        negative_percentage
    )

    for row in range(2, 7):
        worksheet['D{}'.format(row)].font = Font(bold=True)
        worksheet['D{}'.format(row)].fill = summary_fill

    # --------------------------------------------------------
    # FEEDBACK TABLE
    # --------------------------------------------------------

    header_row = 8

    headers = [
        'Student Name',
        'Student Email',
        'Rating',
        'Feedback',
        'Sentiment',
        'Sentiment Score',
        'Submitted Date',
        'Submitted Time'
    ]

    for column, header in enumerate(headers, start=1):
        cell = worksheet.cell(
            row=header_row,
            column=column
        )
        cell.value = header
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment

    current_row = header_row + 1

    for feedback in feedbacks:

        values = [
            feedback.student.name,
            feedback.student.email,
            feedback.rating,
            feedback.feedback_text,
            feedback.sentiment,
            feedback.sentiment_score,
            feedback.created_at.strftime('%d-%m-%Y'),
            feedback.created_at.strftime('%I:%M %p')
        ]

        for column, value in enumerate(values, start=1):
            cell = worksheet.cell(
                row=current_row,
                column=column
            )
            cell.value = value
            cell.alignment = wrap_alignment

        current_row += 1

    # --------------------------------------------------------
    # COLUMN WIDTHS
    # --------------------------------------------------------

    widths = {
        'A': 24,
        'B': 34,
        'C': 12,
        'D': 65,
        'E': 16,
        'F': 18,
        'G': 18,
        'H': 18
    }

    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width

    worksheet.freeze_panes = 'A9'

    # Apply borders/alignment through simple cell formatting.
    for row in worksheet.iter_rows(
        min_row=header_row,
        max_row=max(current_row - 1, header_row),
        min_col=1,
        max_col=8
    ):
        for cell in row:
            cell.alignment = center_alignment if cell.row == header_row else wrap_alignment

    response = HttpResponse(
        content_type=(
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet'
        )
    )

    filename = '{}_feedback.xlsx'.format(
        course.name.replace(' ', '_')
    )

    response[
        'Content-Disposition'
    ] = 'attachment; filename="{}"'.format(filename)

    workbook.save(response)

    return response
