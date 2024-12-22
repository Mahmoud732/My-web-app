from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, FileResponse, Http404
from django.contrib import messages
from .Validations import (
    token_validity,
    is_valid_spotify_url,
)
from .AppProcesses import (
    audio_download_process,
    handle_spotify_url,
    handle_youtube_url,
    handle_spotify_download
)
from .Youtube_apis import get_video_audio_format, download_video
from .models import Media, Playlist
from django.contrib.auth.models import User
from checkout.models import Order
from registration.models import UserProfile
import os
import re


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
    return render(request, 'downloader/browse_playlists.html', {'playlists': data})


def browse_media(request, username, playlist_name):
    user = get_object_or_404(User, username=username)
    playlist = get_object_or_404(Playlist, user=user, title=playlist_name)
    media_files = Media.objects.filter(playlist=playlist)
    
    return render(request, 'downloader/browse_media.html', {'user': user, 'playlist': playlist, 'media_files': media_files})


# Simplify token validation logic
@login_required
def is_validate_token(request, email, token):
    validity = token_validity(email, token)
    if not validity:
        messages.error(request, "Invalid token. Please log in again.")
        return False
    return True

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@login_required
def fetch_info(request):
    if request.method == 'POST':
        try:
            url = request.POST.get('video_link')

            user_data = get_object_or_404(UserProfile, user=request.user)
            last_order = Order.objects.filter(customer=request.user).order_by('-order_date').first()
            email = user_data.user.email
            try:
                token = last_order.token.token
            except:
                messages.error(request, "Invalid token. Please Buy a one.")
                return redirect('Shop')
            
            if not is_validate_token(request, email, token):
                return redirect('Login_Page')
            
            if is_valid_spotify_url(url):
                context = handle_spotify_url(url)
                return render(request, 'downloader/InfoPage.html', context)

            video_info = handle_youtube_url(url)
            context = {
                'video_info': video_info,
                'url': url,
            }

            return render(request, 'downloader/InfoPage.html', context)

        except Exception as e:
            messages.error(request, f"Error fetching information: {e}")
            return redirect('Login_Page')

    return render(request, 'downloader/InfoPage.html')


@login_required
def handle_download(request):
    if request.method == 'POST':
        try:
            # Fetch data from request
            url = request.POST.get('video_link')
            if not url:
                messages.error(request, "Video link is required.")
                return redirect('fetch_info_page')

            resolution = request.POST.get('quality')  # E.g., '1920'
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
                return redirect('Login_Page')

            messages.success(request, "Download started successfully!")

            # Determine file path
            downloaded_file_path = None
            if is_valid_spotify_url(url):
                downloaded_file_path = handle_spotify_download(url, dest)
            elif mediatype == "audio":
                downloaded_file_path = audio_download_process(request, url, dest)
            else:
                video_format, audio_format = get_video_audio_format(request, url, resolution)
                if video_format and audio_format:
                    downloaded_file_path = download_video(request, url, video_format, audio_format, dest)

            if not downloaded_file_path or not os.path.isfile(downloaded_file_path):
                messages.error(request, "The downloaded file could not be found.")
                return redirect('error_page')
            
            title = downloaded_file_path.split("\\")[-1]
            # After successful download, add the video to the user's playlist
            playlist_title = "Singles"  # Default playlist title, can be customized
            playlist, created = Playlist.objects.get_or_create(user=request.user, title=playlist_title)

            # Create a Video object and associate it with the playlist
            media = Media.objects.create(
                playlist=playlist,
                title=title,
                url=url,
                resolution=resolution,
                file_path=downloaded_file_path  # Store the file path of the downloaded video
            )

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
    return render(request, 'downloader/success.html')  # Make sure this template exists


def download_file(request, file_path):
    # The file path should be secure and validated.
    full_path = os.path.join('downloads', file_path)

    if not os.path.exists(full_path):
        raise Http404("File not found.")

    response = FileResponse(open(full_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response