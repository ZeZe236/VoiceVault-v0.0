from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class Registration(models.Model):
    name=models.CharField(max_length=100)
    email=models.CharField(max_length=100)
    phno=models.CharField(max_length=100)
    gender=models.CharField(max_length=100)
    dob=models.DateField()
    photo=models.CharField(max_length=500)
    country=models.CharField(max_length=100)
    USER=models.OneToOneField(User,on_delete=models.CASCADE)


class Audio(models.Model):
    date = models.DateField(null=True, blank=True)
    audio = models.CharField(max_length=500, blank=True, default='')
    audio_file = models.FileField(upload_to='voice_uploads/', null=True, blank=True)
    filename = models.CharField(max_length=255, blank=True, default='')
    filesize = models.BigIntegerField(default=0)
    REGISTRATION = models.ForeignKey(Registration, on_delete=models.CASCADE)


class Complaints(models.Model):
    date = models.DateField()
    complaint=models.CharField(max_length=500)
    reply=models.CharField(max_length=500)
    status=models.CharField(max_length=100)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_complaint_id = models.PositiveIntegerField(default=0)
    REGISTRATION = models.ForeignKey(Registration, on_delete=models.CASCADE)


class LockedApp(models.Model):
    """Records which apps a user has chosen to protect with their voice passphrase."""
    app_key  = models.CharField(max_length=50)
    app_name = models.CharField(max_length=100)
    icon     = models.CharField(max_length=20)
    is_locked = models.BooleanField(default=False)
    REGISTRATION = models.ForeignKey(Registration, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('app_key', 'REGISTRATION')


class LockedDocument(models.Model):
    """A document/file uploaded by the user that can be protected behind voice auth."""
    name       = models.CharField(max_length=255)
    file       = models.FileField(upload_to='locked_docs/')
    file_type  = models.CharField(max_length=50, blank=True, default='')
    filesize   = models.BigIntegerField(default=0)
    uploaded_at = models.DateField(auto_now_add=True)
    is_locked  = models.BooleanField(default=True)
    REGISTRATION = models.ForeignKey(Registration, on_delete=models.CASCADE)


