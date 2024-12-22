from django.db import models
from django.contrib.auth.models import User

class Playlist(models.Model):
    user = models.ForeignKey(User, related_name='playlists', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Media(models.Model):
    playlist = models.ForeignKey(Playlist, related_name='media', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    url = models.URLField()
    resolution = models.CharField(max_length=50)
    file_path = models.CharField(max_length=1024)

    def __str__(self):
        return self.file_name
