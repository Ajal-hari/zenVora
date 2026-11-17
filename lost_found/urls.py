
from django.urls import path
from . import views

urlpatterns = [

    # ========================================================
    # STUDENT LOST & FOUND
    # ========================================================

    path(
        '',
        views.item_list,
        name='lost_found_list'
    ),

    path(
        'book/<int:item_id>/',
        views.book_item,
        name='lost_found_book'
    ),

    # ========================================================
    # ADMIN LOST & FOUND
    # ========================================================

    path(
        'admin/',
        views.admin_items,
        name='lost_found_admin'
    ),

    path(
        'admin/add/',
        views.admin_add_item,
        name='lost_found_add'
    ),

    path(
        'admin/edit/<int:item_id>/',
        views.admin_edit_item,
        name='lost_found_edit'
    ),

    path(
        'admin/delete/<int:item_id>/',
        views.admin_delete_item,
        name='lost_found_delete'
    ),

    path(
        'admin/return/<int:booking_id>/',
        views.admin_return_item,
        name='lost_found_return'
    ),

    path(
        'admin/cancel/<int:booking_id>/',
        views.admin_cancel_booking,
        name='lost_found_cancel'
    ),

]
