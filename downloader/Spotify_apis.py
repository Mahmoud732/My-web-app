
from .Appsecurity import *
import os
import sys
import base64
import json
from requests import get, post

def generate_auth_url():
    """Generate Spotify authorization URL."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI')
    scope = "playlist-read-private playlist-read-collaborative"

    auth_url = (
        f"https://accounts.spotify.com/authorize"
        f"?response_type=code&client_id={client_id}"
        f"&scope={scope.replace(' ', '%20')}"
        f"&redirect_uri={redirect_uri}"
    )
    return auth_url

def get_token_from_code(auth_code):
    """Exchange authorization code for access and refresh tokens."""
    client_id = sensitive_data['SPOTIFY_CLIENT_ID']
    client_secret = sensitive_data['SPOTIFY_CLIENT_SECRET']
    redirect_uri = sensitive_data['SPOTIFY_REDIRECT_URI']

    url = "https://accounts.spotify.com/api/token"
    auth_string = client_id + ":" + client_secret
    auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri
    }

    response = post(url, headers=headers, data=data)

    if response.status_code != 200:
        pass

    return response.json()  # Contains 'access_token' and 'refresh_token'

def get_token_from_refresh(refresh_token):
    """Refresh the access token."""
    client_id = sensitive_data['SPOTIFY_CLIENT_ID']
    client_secret = sensitive_data['SPOTIFY_CLIENT_SECRET']

    url = "https://accounts.spotify.com/api/token"
    auth_string = client_id + ":" + client_secret
    auth_base64 = base64.b64encode(auth_string.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {auth_base64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    response = post(url, headers=headers, data=data)

    if response.status_code != 200:
        pass

    return response.json()['access_token']

def get_auth_header(token):
    """Generate the authorization header."""
    return {"Authorization": f"Bearer {token}"}

def get_spotify_info_of(type, id, extra="", token=None):
    """Fetch information from Spotify API."""
    if token is None:
        raise ValueError("Access token is missing")
    url = f"https://api.spotify.com/v1/{type}/{id}/{extra}"
    headers = get_auth_header(token)
    # Debug: print the token for verification
    print(f"Using token: {token}")
    result = get(url, headers=headers)
    if result.status_code != 200:
        print(f"Error: {result.status_code}, {result.text}")
        return None
    return result.json()

def get_spotify_track_info(track_id, access_token): 
    track = get_spotify_info_of("tracks", track_id, token=access_token)
    track_name = track['name']
    artist_name = track['artists'][0]['name']
    return [{'track_name': track_name, 'artist_name': artist_name}]

def get_spotify_album_tracks_info(album_id, access_token):
    """Fetch tracks from a Spotify album."""
    album_name = get_spotify_info_of("albums", album_id, token=access_token)['name']
    album_tracks = get_spotify_info_of("albums", album_id, "tracks", token=access_token)
    print(album_name)
    return {'album_name':album_name, 'tracks':[
        {'track_name': track['name'], 'artist_name': track['artists'][0]['name']}
        for track in album_tracks['items']
    ]}

def get_spotify_artist_top_tracks(artist_id, access_token):
    """Fetch all albums and their tracks for a Spotify artist."""
    artist_name = get_spotify_info_of('artists', artist_id, token=access_token)['name']
    tracks = get_spotify_info_of('artists', artist_id, 'top-tracks', token=access_token)
    return {'artist':artist_name, 'tracks':[
        {'track_name': track['name'], 'artist_name': track['artists'][0]['name']}
        for track in tracks['tracks']
    ]}

def get_spotify_playlist_tracks(playlist_id, access_token):
    """Fetch all tracks from a Spotify playlist."""
    playlist_info = get_spotify_info_of('playlists', playlist_id, token=access_token)
    playlist_name = playlist_info['name']

    tracks = get_spotify_info_of("playlists", playlist_id, "tracks", token=access_token)

    track_info = []
    for item in tracks['items']:
        track_name = item['track']['name']
        artist_name = item['track']['artists'][0]['name']
        track_info.append({'track_name': track_name, 'artist': artist_name})

    return {'playlist_name': playlist_name, 'tracks': track_info}
