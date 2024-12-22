from .models import Media, Playlist
from django.contrib import messages
from youtubesearchpython import VideosSearch
import yt_dlp
import os


def search_youtube(query):
    try:
        videos_search = VideosSearch(query, limit=1)
        result = videos_search.result().get('result', [])
        return result[0]['link'] if result else None
    except Exception as e:
        return None


def get_audio_format(request, url):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        
        audio_format = next((fmt for fmt in info['formats'] if fmt.get('acodec') != 'none'), None)

        if not audio_format:
            messages.error(request, "No audio track available for this video.")
        return audio_format
    except Exception as e:
        messages.error(request, f"Error fetching audio format: {e}")
        return None


def get_video_audio_format(request, url, resolution):
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        video_format = next(
            (fmt for fmt in info['formats'] 
             if fmt.get('height') and fmt.get('ext') == 'mp4' and f"{fmt.get('height')}p" == resolution),
            None
        )
        if not video_format:
            messages.error(request, f"Resolution {resolution} is not available for this video.")
            return None

        audio_format = next((fmt for fmt in info['formats'] if fmt.get('acodec') != 'none'), None)
        if not audio_format:
            messages.error(request, "No audio track available for this video.")
            return None

        return video_format, audio_format
    except Exception as e:
        messages.error(request, f"Error fetching formats: {e}")
        return None


def download_audio(request, url, audio_format, dest, playlist='Singles'):
    try:
        ydl_opts = {
            'format': f"{audio_format['format_id']}",
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
            'outtmpl': f"{dest}/%(title)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            file = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + '.mp3'
            ydl.download([url])
            absolute_path = os.path.abspath(filename)
            messages.success(request, "Audio download completed!")

            # Create a Video object and associate it with the playlist
            media = Media.objects.create(
                playlist=playlist,
                title=file,
                url=url,
                resolution='Ultra',
                file_path=absolute_path  # Store the file path of the downloaded video
            )
            return
    except Exception as e:
        messages.error(request, f"Error during audio download: {e}")
        return None


def download_video(request, url, video_format, audio_format, dest):
    try:
        ydl_opts = {
            'format': f"{video_format['format_id']}+{audio_format['format_id']}",
            'merge_output_format': 'mp4',
            'outtmpl': f"{dest}/%(title)s - [%(height)s]p.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            filename = ydl.prepare_filename(info)
            ydl.download([url])
            absolute_path = os.path.abspath(filename)
            messages.success(request, "Video download completed!")
            if not absolute_path or not os.path.isfile(absolute_path):
                messages.error(request, "The downloaded file could not be found.")
            
            title = absolute_path.split("\\")[-1]
            # After successful download, add the video to the user's playlist
            playlist_title = "Singles"  # Default playlist title, can be customized
            playlist, created = Playlist.objects.get_or_create(user=request.user, title=playlist_title)

            # Create a Video object and associate it with the playlist
            media = Media.objects.create(
                playlist=playlist,
                title=title,
                url=url,
                resolution='%(height)s',
                file_path=absolute_path  # Store the file path of the downloaded video
            )
            return
    except Exception as e:
        messages.error(request, f"Error during video download: {e}")
        return None
