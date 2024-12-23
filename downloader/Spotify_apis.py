from django.shortcuts import redirect
from django.http import HttpResponse, JsonResponse
from registration.models import UserProfile
from .Appsecurity import *
import os
import base64
from requests import get, post
from dotenv import load_dotenv


load_dotenv()

def generate_auth_url():
    """Generate Spotify authorization URL."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    redirect_uri = "http://localhost:8000/callback"
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
    redirect_uri = 'http://localhost:8000/callback'

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
    print(response.json())
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

def get_token(request, user_data):
    if user_data.refresh_token:
        # Use existing refresh token to get access token
        access_token = get_token_from_refresh(user_data.refresh_token)
    else:
        # No refresh token exists, retrieve new tokens and save refresh token
        my_data = retrieve_tokens(request)
        refresh_token = my_data.get('refresh_token')
        access_token = my_data.get('access_token')
        
        # Save the new refresh token to the user's profile
        user_data.refresh_token = refresh_token
        user_data.save()
    return access_token



def start_authentication(request):
    """Generate and return the Spotify authentication URL."""
    auth_url = generate_auth_url()
    return auth_url

def authenticate_user(request):
    """Start the Spotify authentication process."""
    request.session.pop('auth_code', None)  # Clear any previous auth code
    return start_authentication(request)

def retrieve_tokens(request):
    """Exchange the authorization code for tokens and save the refresh token."""
    # Start the authentication process if not already done
    if not request.session.get('auth_code'):
        return authenticate_user(request)  # Redirect if no auth code is found
    
    code = request.session.get('auth_code')

    if not code:
        return HttpResponse("Authorization code not found!", status=400)

    try:
        tokens = get_token_from_code(code)
        print(tokens)
        access_token = tokens['access_token']
        refresh_token = tokens['refresh_token']
        
        # Save the refresh token to the user's profile
        save_refresh_token(request.user, refresh_token)
        
        response_data = {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

        return JsonResponse(response_data)  # Returning as JSON
        
    except Exception as e:
        return HttpResponse(f"Error retrieving tokens: {str(e)}", status=500)

def spotify_callback(request):
    """Handle the Spotify redirect and retrieve the authorization code."""
    code = request.GET.get('code', None)
    if code:
        request.session['auth_code'] = code  # Store the code in the session
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.is_spotify_autherized = True
        profile.save()

        return redirect('Home_Page')
    return HttpResponse("Authorization code not found!", status=400)

def save_refresh_token(user, refresh_token):
    """Save the refresh token to the UserProfile."""
    profile, created = UserProfile.objects.get_or_create(user=user)
    profile.refresh_token = refresh_token
    profile.save()

def get_refresh_token(user):
    """Get the refresh token from the UserProfile."""
    try:
        profile = UserProfile.objects.get(user=user)
        return profile.refresh_token
    except UserProfile.DoesNotExist:
        return None




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

    result = get(url, headers=headers)
    if result.status_code != 200:
        print(f"Error: {result.status_code}, {result.text}")
        return None
    return result.json()

def get_spotify_track_info(track_id, access_token): 
    """Fetch a single track's info."""
    track = get_spotify_info_of("tracks", track_id, token=access_token)

    track_name = track['name']
    artist_name = track['artists'][0]['name']
    thumbnail = track['album']['images'][0]['url']  # Album image for the track
    
    return {'thumbnail': thumbnail, 'track_name': track_name, 'artist_name': artist_name}

def get_spotify_album_tracks_info(album_id, access_token):
    """Fetch tracks and thumbnail for a Spotify album."""
    album_data = get_spotify_info_of("albums", album_id, token=access_token)

    album_thumbnail = album_data['images'][0]['url']
    album_name = album_data['name']

    album_tracks = album_data['tracks']['items']
    tracks = [
        {'track_name': track['name'], 'artist_name': track['artists'][0]['name']}
        for track in album_tracks
    ]

    return {'thumbnail': album_thumbnail, 'name': album_name, 'tracks': tracks}

def get_spotify_artist_top_tracks(artist_id, access_token):
    """Fetch top tracks for a Spotify artist."""
    artist_data = get_spotify_info_of("artists", artist_id, token=access_token)
    artist_thumbnail = artist_data['images'][0]['url']
    artist_name = artist_data['name']
    
    tracks_data = get_spotify_info_of('artists', artist_id, 'top-tracks', token=access_token)

    tracks = [
        {'track_name': track['name'], 'artist_name': track['artists'][0]['name']}
        for track in tracks_data['tracks']
    ]

    return {'thumbnail': artist_thumbnail, 'name': artist_name, 'tracks': tracks}

def get_spotify_playlist_tracks(playlist_id, access_token):
    """Fetch all tracks from a Spotify playlist."""
    playlist_data = get_spotify_info_of('playlists', playlist_id, token=access_token)
    playlist_thumbnail = playlist_data['images'][0]['url']
    playlist_name = playlist_data['name']

    tracks_data = playlist_data['tracks']['items']

    tracks = [
        {
            'track_name': item['track']['name'],
            'artist_name': item['track']['artists'][0]['name'],
            'thumbnail': item['track']['album']['images'][0]['url']  # Thumbnail for each track
        }
        for item in tracks_data
    ]

    return {'thumbnail': playlist_thumbnail, 'name': playlist_name, 'tracks': tracks}
