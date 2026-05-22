from django.db import models

# Create your models here.
class Resume(models.Model):
    # Stores the uploaded resume file
    file=models.FileField(upload_to='resumes/')
    uploaded_at=models.DateTimeField(auto_now_add=True)