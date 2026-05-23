from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
 
urlpatterns = [
    # Home
    path('', views.home, name='home'),
 
    # Auth
    path('login/',       views.login_view,    name='login'),
    path('logout/',      views.logout_view,   name='logout'),
    path('signed-out/',  views.logout_confirm, name='logout_confirm'),
    path('register/',    views.register_view,  name='register'),
 
    # Password reset (Django built-in views, just needs templates)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='analyzer/password_reset.html'
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='analyzer/password_reset_done.html'
         ),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='analyzer/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='analyzer/password_reset_complete.html'
         ),
         name='password_reset_complete'),
 
    # Resume
    path('upload/',       views.resume_upload, name='resume_upload'),
    path('download-pdf/', views.download_pdf,  name='download_pdf'),
 
    # Admin dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]
 
