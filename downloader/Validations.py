from django.contrib import messages
from .Appsecurity import * 
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime
from pytz import UTC
import re

# MongoDB setup
client = MongoClient(sensitive_data['MONGO_URI'], server_api=ServerApi('1'))
db = client['auth_app']
tokens_collection = db['tokens']
print()

def is_valid_spotify_url(url):
    """Check if the URL is a valid Spotify playlist"""
    return re.match(r"https://open.spotify.com/\w+", url) is not None


def is_valid_spotify_album_url(url):
    """تحقق مما إذا كان الرابط صالحًا لقائمة تشغيل سبوتيفاي"""
    return re.match(r"https://open.spotify.com/album/\w+", url) is not None


def is_valid_spotify_playlist_url(url):
    """تحقق مما إذا كان الرابط صالحًا لقائمة تشغيل سبوتيفاي"""
    return re.match(r"https://open.spotify.com/playlist/\w+", url) is not None


def is_valid_spotify_artist_url(url):
    """تحقق مما إذا كان الرابط صالحًا لقائمة تشغيل سبوتيفاي"""
    return re.match(r"https://open.spotify.com/artist/\w+", url) is not None

def token_validity(email, token):
    if not token:
        return False
    # Fetch token data from the database
    token_data = tokens_collection.find_one({"token": token})
    if not token_data:
        return False
    # Ensure `expires_at` is timezone-aware
    if token_data.get('expiresAt').tzinfo is None:
        token_data['expiresAt'] = token_data['expiresAt'].replace(tzinfo=UTC)
    if datetime.now(UTC) > token_data['expiresAt']:
        return False
    # Validate user_id
    if token_data.get('user_id') and token_data['user_id'] != email:
        return False
    return True