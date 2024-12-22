from django.contrib import messages

# Sensitive data to store
sensitive_data = {
    "MONGO_URI": "mongodb+srv://mahmed732005:ddEcRyduRgwFmc3v@cluster0.r9g62.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    "SECRET_PASSWORD": "MahmoudTaha364",
    "SPOTIFY_CLIENT_ID": "b36e01c92fc24dc6a59ea167fd59ed13",
    "SPOTIFY_CLIENT_SECRET": "928fe934165a48db80ea54a8e4205e6b",
    "SPOTIFY_REDIRECT_URI": "http://localhost:8888/callback"
}


def authenticate(request, password: str):
    """Check if the provided password matches."""

    password = password.strip()

    if str(password) != sensitive_data['SECRET_PASSWORD']:
        messages.error(request, "Authentication failed! Invalid password.")
        return