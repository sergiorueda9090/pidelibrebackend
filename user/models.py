import uuid
import os
from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
def user_image_path(instance, filename):
    ext = filename.split('.')[-1]  # get file extension
    unique_filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("user_image", unique_filename)


class User(AbstractUser):
    profile_image = models.ImageField(
        upload_to=user_image_path,
        null=True,
        blank=True
    )
