from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    birthday = models.DateField(null=True)
    is_loggedin = models.BooleanField(default=False)
    token = models.TextField(null=True, unique=True)
    refresh_token = models.TextField(null=True, unique=True)
    is_spotify_autherized = models.BooleanField(default=False)
    # proxy = models.CharField(max_length=255, null=True, blank=True)  # New field for proxy


    def get_age(self):
        if self.birthday is not None:
            now = datetime.now()
            age = now.year - self.birthday.year
            if (now.month, now.day) < (self.birthday.month, self.birthday.day):
                age -= 1
            return age
        return None
    

    def __str__(self):
        return f'{self.user.username} ({self.user.email})'

