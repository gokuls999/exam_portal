from django.db import models

class Admin(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)  # Store hashed password later

    def __str__(self):
        return self.username

# Create your models here.
