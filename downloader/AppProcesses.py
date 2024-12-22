from .Spotify_apis import (
    get_spotify_artist_top_tracks,
    get_spotify_playlist_tracks,
    get_spotify_album_tracks_info,
    get_spotify_track_info
)
from .Validations import (
    is_valid_spotify_artist_url,
    is_valid_spotify_playlist_url,
    is_valid_spotify_album_url
)
from .AppServer import authenticate_user, get_refresh_token_from_registry, get_token_from_refresh
from .Youtube_apis import search_youtube, download_audio, get_audio_format
from django.contrib import messages
import yt_dlp
import concurrent.futures
import asyncio

def handle_spotify_url(url):
    try:
        if is_valid_spotify_artist_url(url):
            albums = get_spotify_artist_top_tracks(url)
            return {"type": "artist", "albums": albums} if albums else {"error": "No albums found for this artist."}

        if is_valid_spotify_playlist_url(url):
            tracks = get_spotify_playlist_tracks(url)
            return {"type": "playlist", "tracks": tracks} if tracks else {"error": "No tracks found in the playlist."}

        if is_valid_spotify_album_url(url):
            tracks = download_album_tracks(url)
            return {"type": "album", "tracks": tracks} if tracks else {"error": "No tracks found in the album."}

    except Exception as e:
        return {"error": f"Error handling Spotify URL: {e}"}

def handle_youtube_url(url):
    try:
        ydl_opts = {
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

def handle_spotify_download(url, dest):
    try:
        spotify_id = url.split("/")[-1].split("?")[0]
        if is_valid_spotify_playlist_url(url):
            download_spotify_playlist_tracks(spotify_id, dest)
        elif is_valid_spotify_album_url(url):
            download_album_tracks(spotify_id, dest)
        elif is_valid_spotify_artist_url(url):
            download_artist_top_tracks(spotify_id, dest)
        else:
            download_spotify_track(spotify_id, dest)
    except Exception as e:
        raise Exception(f"Spotify download error: {e}")

def process_and_download_track(track_name, artist_name, dest):
    try:
        if not track_name or not artist_name:
            raise ValueError("Missing track or artist name.")

        song_query = f"{track_name} {artist_name}"
        youtube_id = search_youtube(song_query)
        if not youtube_id:
            raise ValueError("No YouTube ID found for the query.")

        audio_format = get_audio_format(youtube_id)
        download_audio(youtube_id, audio_format, dest, progress_callback=lambda p: print(f"Download progress: {p}%"))
    except Exception as e:
        raise Exception(f"Error processing track '{track_name}': {e}")

def process_and_download_tracks(tracks, dest, context=""):
    total_tracks = len(tracks)
    messages.info(None, f"Starting download of {total_tracks} tracks {context}.")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        tasks = []
    for index, track in enumerate(tracks, start=1):
            task = asyncio.create_task(process_and_download_track(
                track.get("track_name"),
                track.get("artist_name"),
                dest
            ))
            tasks.append(task)
            messages.info(None, f"Queued: {track.get('track_name')} ({index}/{total_tracks})")
        
    completed = []
    for task in asyncio.as_completed(tasks):
        try:
            task
            completed.append(task)
            messages.info(None, f"Progress: {len(completed)}/{total_tracks} tracks completed")
        except Exception as e:
            messages.error(None, f"Error during download: {e}")

def download_spotify_track(id, dest):
    try:
        access_token = get_token_from_refresh(get_refresh_token_from_registry())
    except:
        access_token, _ = authenticate_user()

    track_info = get_spotify_track_info(id, access_token)
    process_and_download_tracks([track_info], dest, context="(Single Track)")

def download_album_tracks(id, dest):
    try:
        access_token = get_token_from_refresh(get_refresh_token_from_registry())
    except:
        access_token, _ = authenticate_user()

    album_data = get_spotify_album_tracks_info(id, access_token)
    album_name = album_data['album_name']
    tracks = album_data['tracks']
    process_and_download_tracks(tracks, dest, context=f"from album '{album_name}'")

def download_artist_top_tracks(id, dest):
    try:
        access_token = get_token_from_refresh(get_refresh_token_from_registry())
    except:
        access_token, _ = authenticate_user()

    artist_data = get_spotify_artist_top_tracks(id, access_token)
    artist_name = artist_data['artist']
    tracks = artist_data['tracks']
    process_and_download_tracks(tracks, dest, context=f"for artist '{artist_name}'")

def download_spotify_playlist_tracks(playlist_id, dest):
    try:
        access_token = get_token_from_refresh(get_refresh_token_from_registry())
    except:
        access_token, _ = authenticate_user()

    playlist_data = get_spotify_playlist_tracks(playlist_id, access_token)
    playlist_name = playlist_data['playlist_name']
    tracks = playlist_data['tracks']
    process_and_download_tracks(tracks, dest, context=f"from playlist '{playlist_name}'")

def audio_download_process(request, url, dest):
    if url:
        audio_format = get_audio_format(request, url)
        messages.success(request, "Starting Download...")
        file_name = download_audio(request, url, audio_format, dest)
        messages.success(request, "Download Complete!")
        return file_name
    else:
        messages.error(request, "Track not found")