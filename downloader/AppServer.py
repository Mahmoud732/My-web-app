from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from .Spotify_apis import generate_auth_url, get_token_from_code
from registration.models import UserProfile

def start_authentication(request):
    """Generate and redirect the user to the Spotify authentication URL."""
    auth_url = generate_auth_url()
    request.session.flush()  # Clear the session before redirecting
    return HttpResponseRedirect(auth_url)

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
        return HttpResponse("Authorization code received! You can close this window.")
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
