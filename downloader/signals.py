from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from .models import Playlist
import os
import shutil

@receiver(user_logged_out)
def delete_downloaded_playlists(sender, request, user, **kwargs):
    """Delete the downloaded playlists when the user logs out."""
    try:
        # Fetch playlists downloaded by the user
        playlists = Playlist.objects.filter(user=user)
        
        # Delete the files and playlists
        for playlist in playlists:
            # Assuming download_path is the path where the playlist is stored
            if os.path.exists(playlist.download_path):
                shutil.rmtree(playlist.download_path)  # Remove directory and its contents

            # Delete the playlist record from the database
            playlist.delete()

    except Exception as e:
        print(f"Error deleting downloaded playlists: {str(e)}")
