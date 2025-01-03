from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.contrib import messages
from .Validations import (
    token_validity,
    is_valid_spotify_url,
)
from .AppProcesses import (
    audio_download_process,
    handle_spotify_url,
    handle_spotify_download
)
from .Spotify_apis import (
    get_token,
    retrieve_tokens
)
from .Youtube_apis import get_video_audio_format, download_video, handle_youtube_url
from .models import Media, Playlist
from django.contrib.auth.models import User
from checkout.models import Order
from registration.models import UserProfile
import os
import re


@login_required
def Authorization_spotify(request):
    if request.method == 'POST':
        user_data = get_object_or_404(UserProfile, user=request.user)
        auth_url = retrieve_tokens(request)
        return JsonResponse({"auth_url":auth_url})
    return render(request, 'Downloader/InfoPage.html', {'user_data': user_data})


@login_required
def browse_playlists(request):
    user = request.user  # Get the logged-in user
    playlists = Playlist.objects.filter(user=user).prefetch_related('media')
    data = []
    for playlist in playlists:
        data.append({
            'title': playlist.title,
            'description': playlist.description,
            'media': [
                {
                    'title': os.path.basename(media.title),
                    'url': media.url,
                    'resolution': media.resolution,
                    'download_url': media.file_path
                }
                for media in playlist.media.all()
            ]
        })
    return render(request, 'Downloader/browse_playlists.html', {'playlists': data})


def browse_media(request, username, playlist_name):
    user = get_object_or_404(User, username=username)
    playlist = get_object_or_404(Playlist, user=user, title=playlist_name)
    media_files = Media.objects.filter(playlist=playlist)
    
    return render(request, 'Downloader/browse_media.html', {'user': user, 'playlist': playlist, 'media_files': media_files})


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@login_required
def fetch_info(request):
    user_data = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        try:
            url = request.POST.get('media_link')

            # Get the user data and validate the order token
            user_data = get_object_or_404(UserProfile, user=request.user)
            last_order = Order.objects.filter(customer=request.user).order_by('-order_date').first()
            email = user_data.user.email

            # Get the token from the order, if it exists
            try:
                token = last_order.token.token
            except:
                messages.error(request, "Invalid token. Please buy one.")
                return redirect('Shop')
            
            if not is_validate_token(request, email, token):
                return redirect('login')
            # Handle refresh token logic

            # Handle Spotify URL
            if is_valid_spotify_url(url):
                print("access_token")
                access_token = get_token(request, user_data)
                context = handle_spotify_url(url, access_token)
                context = {
                'user_data': user_data,
                'spotify_info': context,
                'url': url,
                'quality': 'Ultra',
                }
                return render(request, 'Downloader/InfoPage.html', context)

            # Handle YouTube URLs as well
            video_info = handle_youtube_url(request, url)
            context = {
                'user_data': user_data,
                'video_info': video_info,
                'url': url,
            }

            return render(request, 'Downloader/InfoPage.html', context)

        except Exception as e:
            messages.error(request, f"Error fetching information: {e}")
            return redirect('login')
    return render(request, 'Downloader/InfoPage.html', {'user_data': user_data})


@login_required
def handle_download(request):
    if request.method == 'POST':
        try:
            # Fetch data from request
            url = request.POST.get('media_link')

            if not url:
                messages.error(request, "Video link is required.")
                return redirect('fetch_info_page')

            resolution = request.POST.get('quality')
            dest = os.path.abspath('./downloads')
            mediatype = request.POST.get('media_type', 'video')
            custom_filename = request.POST.get('custom_filename', '')
            title = sanitize_filename(custom_filename) if custom_filename else ''

            user_data = get_object_or_404(UserProfile, user=request.user)
            last_order = Order.objects.filter(customer=request.user).order_by('-order_date').first()
            email = user_data.user.email
            try:
                token = last_order.token.token
            except:
                messages.error(request, "Invalid token. Please Buy a one.")
                return redirect('Shop')
            
            if not is_validate_token(request, email, token):
                return redirect('login')

            messages.success(request, "Download started successfully!")

            # Determine file path
            if is_valid_spotify_url(url):
                access_token = get_token(request, user_data)
                handle_spotify_download(request, url, dest, access_token)
            elif mediatype == "audio":
                audio_download_process(request, url, dest)
            else:
                video_format, audio_format = get_video_audio_format(request, url, resolution)
                if video_format and audio_format:
                    download_video(request, url, resolution, video_format, audio_format, dest)

            # Optionally, you can return a response to show the video details or a success message
            messages.success(request, f"Video '{title}' added to your playlist!")
            return redirect('browse_playlists')  # Redirect to the success page or a relevant page

        except Exception as e:
            print(f"Error in handle_download: {str(e)}")
            messages.error(request, f"An unexpected error occurred: {str(e)}")
            return redirect('error_page')

    messages.error(request, "Invalid request method.")
    return redirect('Home_Page')


def success_page(request):
    # Add any logic to display after successful download
    messages.success(request, "Your download was successful!")
    return render(request, 'Downloader/success.html')  # Make sure this template exists


def download_file(request, file_path):
    try:
        # The file path should be secure and validated.
        full_path = os.path.join('downloads', file_path)

        if not os.path.exists(full_path):
            raise Http404("File not found.")

        return FileResponse(open(full_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
    except Exception as e:
        messages.error(request, f"Error downloading file: {str(e)}")
        return redirect('Home_Page')


# Simplify token validation logic
@login_required
def is_validate_token(request, email, token):
    validity = token_validity(email, token)
    if not validity:
        messages.error(request, "Invalid token. Please log in again.")
        return False
    return True