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
from .Youtube_apis import search_youtube, download_audio, get_audio_format
from .models import Playlist
from django.contrib import messages
from asgiref.sync import sync_to_async


def handle_spotify_url(url, access_token):
    id = url.split('/')[-1].split('?')[0]
    try:
        if is_valid_spotify_artist_url(url):
            albums = get_spotify_artist_top_tracks(id, access_token)
            return {"type": "artist", "albums": albums} if albums else {"error": "No albums found for this artist."}

        elif is_valid_spotify_playlist_url(url):
            tracks = get_spotify_playlist_tracks(id, access_token)
            return {"type": "playlist", "tracks": tracks} if tracks else {"error": "No tracks found in the playlist."}

        elif is_valid_spotify_album_url(url):
            tracks = get_spotify_album_tracks_info(id, access_token)
            return {"type": "album", "tracks": tracks} if tracks else {"error": "No tracks found in the album."}
        else:
            track = get_spotify_track_info(id, access_token)
            return {"type": "Track", "tracks": track} if track else {"error": "No tracks found."}

    except Exception as e:
        return {"error": f"Error handling Spotify URL: {e}"}


def handle_spotify_download(request, url, dest, access_token):
    try:
        spotify_id = url.split("/")[-1].split("?")[0]
        if is_valid_spotify_playlist_url(url):
            download_spotify_playlist_tracks(request, spotify_id, dest, access_token)
        elif is_valid_spotify_album_url(url):
            download_album_tracks(request, spotify_id, dest, access_token)
        elif is_valid_spotify_artist_url(url):
            download_artist_top_tracks(request, spotify_id, dest, access_token)
        else:
            download_spotify_track(request, spotify_id, dest, access_token)
    except Exception as e:
        raise Exception(f"Spotify download error: {e}")

def process_and_download_track(request, track_name, artist_name, dest, Playlist=None):
    try:
        if not track_name or not artist_name:
            raise ValueError("Missing track or artist name.")

        song_query = f"{track_name} {artist_name}"
        youtube_id = search_youtube(request ,song_query)
        if not youtube_id:
            raise ValueError("No YouTube ID found for the query.")

        audio_format = get_audio_format(request, youtube_id)
        download_audio(request, youtube_id, audio_format, dest, playlist=Playlist)
    except Exception as e:
        raise Exception(f"Error processing track '{track_name}': {e}")

import asyncio
from django.contrib import messages

def process_and_download_tracks(request, tracks, dest, context="", playlist=None):
    total_tracks = len(tracks)
    messages.info(request, f"Starting download of {total_tracks} tracks {context}.")
    
    # Wrap the blocking ORM call
    playlist_title = context
    playlist, created = Playlist.objects.get_or_create(user=request.user, title=playlist_title)
    
    completed = []
    for index, track in enumerate(tracks, start=1):
        try:
            process_and_download_track(
                request,
                track.get("track_name"),
                track.get("artist_name"),
                dest,
                playlist
            )
            completed.append(track)
            messages.info(request, f"Queued: {track.get('track_name')} ({index}/{total_tracks})")
        except Exception as e:
            messages.error(request, f"Error queuing track {track.get('track_name')}: {e}")
    
    
    if len(completed) == total_tracks:
        messages.info(request, "All tracks have been successfully downloaded!")
    else:
        messages.error(request, f"Some tracks failed to download. {len(completed)}/{total_tracks} completed.")

def download_spotify_track(request, id, dest, access_token):
    track_info = get_spotify_track_info(id, access_token)
    process_and_download_tracks(request, [track_info], dest, context="(Single Track)")

def download_album_tracks(request, id, dest, access_token):
    album_data = get_spotify_album_tracks_info(id, access_token)
    album_name = album_data['name']
    tracks = album_data['tracks']
    process_and_download_tracks(request, tracks, dest, context=f"from album '{album_name}'")

def download_artist_top_tracks(request, id, dest, access_token):
    artist_data = get_spotify_artist_top_tracks(id, access_token)
    artist_name = artist_data['name']
    tracks = artist_data['tracks']
    process_and_download_tracks(request, tracks, dest, context=f"for artist '{artist_name}'")

def download_spotify_playlist_tracks(request, playlist_id, dest, access_token):
    playlist_data = get_spotify_playlist_tracks(playlist_id, access_token)
    playlist_name = playlist_data['name']
    tracks = playlist_data['tracks']
    process_and_download_tracks(request, tracks, dest, context=f"from playlist '{playlist_name}'")

def audio_download_process(request, url, dest):
    if url:
        audio_format = get_audio_format(request, url)
        messages.success(request, "Starting Download...")
        file_name = download_audio(request, url, audio_format, dest, playlist=None)
        messages.success(request, "Download Complete!")
        return file_name
    else:
        messages.error(request, "Track not found")
