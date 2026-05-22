from django.urls import path

from analyzer import admin
from . import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.resume_upload, name='upload'),
    path('download-pdf', views.download_pdf, name='download_pdf'),
    path('dashboard/', views.dashboard, name='dashboard'),
]