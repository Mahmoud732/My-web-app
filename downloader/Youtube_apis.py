from .models import Media, Playlist
from django.contrib import messages
from django.conf import settings
from googleapiclient.discovery import build
import yt_dlp
import os
from dotenv import load_dotenv

load_dotenv()

def search_youtube(request, query):
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')  # Replace with your actual API key
        youtube = build('youtube', 'v3', developerKey=api_key)

        # Perform the search
        request = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            maxResults=1
        )
        response = request.execute()

        # Extract video link
        if response['items']:
            video_id = response['items'][0]['id']['videoId']
            return f"https://www.youtube.com/watch?v={video_id}"
        else:
            return None
    except Exception as e:
        messages.error(request, f"Error: {e}")
        return None


def handle_youtube_url(url):
    try:
        ydl_opts = {
            "cookies":"cookies.txt",
            "noplaylist": True,
            "format": "bestaudio/best",
            "progress_hooks": [lambda d: print(f'Download Progress: {d["_percent_str"]}')]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            mp4_formats = [fmt for fmt in info['formats'] if fmt.get('height') and fmt.get('ext') == 'mp4']
            resolutions = sorted(set(f"{fmt['height']}p" for fmt in mp4_formats), key=lambda res: int(res.replace("p", "")))
            audio_formats = [fmt for fmt in info['formats'] if not fmt.get('height') and fmt.get('ext') == 'm4a']
            bitrates = sorted(set(f"{int(fmt['abr'])} kbps" for fmt in audio_formats if fmt.get('abr')), key=lambda br: int(br.split()[0]))
            return {
                "thumbnail": info.get('thumbnail', None),
                "duration": info['duration'],
                "uploader": info['uploader'],
                "channel_id": info['channel'],
                "title": info['title'],
                "description": info['description'],
                "views": info['view_count'],
                "upload_date": info['upload_date'],
                "resolutions": resolutions if len(resolutions) > 0 else None,
                "bitrates": bitrates if len(bitrates) > 0 else None,
            }
    except Exception as e:
        return {"error": f"Error handling YouTube URL: {e}"}


def get_audio_format(request, url):
    try:
        with yt_dlp.YoutubeDL({"cookies":"cookies.txt", 'quiet': True}) as ydl:
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
        with yt_dlp.YoutubeDL({"cookies":"cookies.txt", 'quiet': True}) as ydl:
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


def download_audio(request, url, audio_format, dest, playlist):
    try:
        playlist = 'Singles' if playlist is None else playlist
        user_download_folder = os.path.join(settings.MEDIA_ROOT, dest, request.user.username)

        ydl_opts = {
            "cookies":"cookies.txt",
            'format': f"{audio_format['format_id']}",
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
            'outtmpl': f"{user_download_folder}/%(title)s.%(ext)s",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url)
            filename = ydl.prepare_filename(info)
            filename = os.path.splitext(filename)[0] + '.mp3'
            ydl.download([url])
            absolute_path = os.path.abspath(filename)
            messages.success(request, "Audio download completed!")
            title = absolute_path.split("\\")[-1]
            playlist, created = Playlist.objects.get_or_create(user=request.user, title=playlist)
            # Create a Video object and associate it with the playlist
            media = Media.objects.create(
                playlist=playlist,
                title=title,
                url=url,
                resolution='Ultra',
                file_path=absolute_path  # Store the file path of the downloaded video
            )
            return
    except Exception as e:
        messages.error(request, f"Error during audio download: {e}")
        return None


def download_video(request, url, resuloution, video_format, audio_format, dest):
    try:
        user_download_folder = os.path.join(settings.MEDIA_ROOT, dest, request.user.username)

        ydl_opts = {
            "cookies":"cookies.txt",
            'format': f"{video_format['format_id']}+{audio_format['format_id']}",
            'merge_output_format': 'mp4',
            'outtmpl': f"{user_download_folder}/%(title)s - [%(height)s]p.%(ext)s",
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
                resolution= resuloution,
                file_path=absolute_path  # Store the file path of the downloaded video
            )
            return
    except Exception as e:
        messages.error(request, f"Error during video download: {e}")
        return None
