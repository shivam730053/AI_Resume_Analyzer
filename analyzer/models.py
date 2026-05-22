from django.db import models

# Create your models here.
class Resume(models.Model):
    # Stores the uploaded resume file
    file=models.FileField(upload_to='resumes/')
    score=models.TextField(default=0)
    match_percentage=models.TextField(default=0)
    uploaded_at=models.DateTimeField(auto_now_add=True)
    extracted_skills=models.TextField(blank=True)

    def __str__(self):
        return self.file.name