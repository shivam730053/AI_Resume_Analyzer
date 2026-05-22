from django.urls import path
from . import views

urlpatterns = [
    path('', views.resume_upload, name='upload'),
    path('download-pdf', views.download_pdf, name='download_pdf'),
]