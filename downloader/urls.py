from django.urls import path
from . import views, Spotify_apis

urlpatterns = [
    path('', views.fetch_info, name='Home_Page'),
    path('download/', views.handle_download, name='download_page'),
    path('success/', views.success_page, name='success_page'),
    path('authrization', views.Authorization_spotify, name='spotify_auth'),
    path('my-playlists/', views.browse_playlists, name='browse_playlists'),
    path('download/<str:file_path>/', views.download_file, name='download_file'),
    path('callback/', Spotify_apis.spotify_callback, name='spotify_callback'),
    # path('api/playlist-tracks/', views.get_playlist_tracks, name='get_playlist_tracks'),
    # path('api/download-tracks/', views.download_tracks, name='download_tracks'),
]
