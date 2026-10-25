from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views

urlpatterns = [

    path(
        'register/',
        views.register_view,
        name='register'
    ),

    path(
        'verification/',
        views.verification_pending_view,
        name='verification_pending'
    ),

    path(
        'verification/email/',
        views.verify_email_view,
        name='verify_email'
    ),

    path(
        'verification/phone/',
        views.verify_phone_view,
        name='verify_phone'
    ),

    path(
        'verification/email/resend/',
        views.resend_verification_email_view,
        name='resend_verification_email'
    ),

    path(
        'verification/phone/resend/',
        views.resend_phone_code_view,
        name='resend_phone_code'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            email_template_name='users/password_reset_email.html',
            subject_template_name='users/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'password-reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),

    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

]
