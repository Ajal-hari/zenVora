
from django.contrib import admin
from django.urls import path, include

from feedback import views


urlpatterns = [

    # ========================================================
    # DJANGO ADMIN
    # ========================================================

    path(
        'django-admin/',
        admin.site.urls
    ),


    # ========================================================
    # HOME
    # ========================================================

    path(
        '',
        views.home,
        name='home'
    ),


    # ========================================================
    # STUDENT
    # ========================================================

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'verify-otp/',
        views.verify_otp,
        name='verify_otp'
    ),

    path(
        'resend-otp/',
        views.resend_otp,
        name='resend_otp'
    ),

    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),

    path(
        'feedback/',
        views.feedback_view,
        name='feedback'
    ),


    # ========================================================
    # STUDENT FEEDBACK EDIT / DELETE
    # ========================================================

    path(
        'feedback/edit/<int:feedback_id>/',
        views.edit_feedback,
        name='edit_feedback'
    ),

    path(
        'feedback/delete/<int:feedback_id>/',
        views.delete_feedback,
        name='delete_feedback'
    ),


    # ========================================================
    # STUDENT LOGOUT
    # ========================================================

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),


    # ========================================================
    # ADMIN LOGIN
    # ========================================================

    path(
        'admin-login/',
        views.admin_login,
        name='admin_login'
    ),

    path(
        'admin-dashboard/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

    path(
        'admin-logout/',
        views.admin_logout,
        name='admin_logout'
    ),


    # ========================================================
    # ADMIN COURSE MANAGEMENT
    # ========================================================

    path(
        'admin-course/add/',
        views.admin_add_course,
        name='admin_add_course'
    ),

    path(
        'admin-course/update/<int:course_id>/',
        views.admin_update_course,
        name='admin_update_course'
    ),

    path(
        'admin-course/delete/<int:course_id>/',
        views.admin_delete_course,
        name='admin_delete_course'
    ),


    # ========================================================
    # ADMIN FEEDBACK MANAGEMENT
    # ========================================================

    path(
        'admin-feedback/edit/<int:feedback_id>/',
        views.admin_edit_feedback,
        name='admin_edit_feedback'
    ),

    path(
        'admin-feedback/delete/<int:feedback_id>/',
        views.admin_delete_feedback,
        name='admin_delete_feedback'
    ),


    # ========================================================
    # COURSE REPORT DOWNLOAD
    # ========================================================

    path(
        'admin-course/<int:course_id>/download-csv/',
        views.download_course_csv,
        name='download_course_csv'
    ),

    path(
        'admin-course/<int:course_id>/download-pdf/',
        views.download_course_pdf,
        name='download_course_pdf'
    ),

    path(
        'admin-course/<int:course_id>/download-excel/',
        views.download_course_excel,
        name='download_course_excel'
    ),


    # ========================================================
    # NEW ZENVORA LOST & FOUND
    # ========================================================

    path(
        'lost-found/',
        include('lost_found.urls')
    ),

]
