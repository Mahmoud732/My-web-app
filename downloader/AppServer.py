from .Spotify_apis import *
import threading
import webbrowser
import http.server
import socketserver
import urllib.parse
import winreg  # For working with the Windows registry

auth_code = None

# Simple HTTP server to handle the callback and get the authorization code
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"Authorization code received! You can close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization code not found!")

def start_http_server():
    with socketserver.TCPServer(('localhost', 8888), MyHandler) as httpd:
        print("Serving on port 8888...")
        httpd.serve_forever()

def generate_and_open_auth_url():
    url = generate_auth_url()
    webbrowser.open(url)
    print("Authorization URL opened in browser.")

def wait_for_auth_code():
    global auth_code
    while auth_code is None:
        pass
    return auth_code

def save_refresh_token_to_registry(refresh_token):
    try:
        # Open the registry key for the application (or create it if it doesn't exist)
        reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\spotipytube\Credentials\CredentialData")
        binaries = refresh_token.encode('utf-8')
        # Save the refresh token using the correct registry type (REG_SZ for strings)
        winreg.SetValueEx(reg_key, "RefreshToken", 0, winreg.REG_BINARY, binaries)
        
        # Close the registry key
        winreg.CloseKey(reg_key)
        print("Refresh token saved to registry.")
    except Exception as e:
        print(f"Error saving refresh token to registry: {e}")

def authenticate_user():
    # Start the HTTP server in a separate thread
    server_thread = threading.Thread(target=start_http_server)
    server_thread.daemon = True
    server_thread.start()

    # Open Spotify auth URL
    generate_and_open_auth_url()

    # Wait for the auth code
    code = wait_for_auth_code()
    print(f"Received Auth Code: {code}")

    # Exchange code for tokens
    tokens = get_token_from_code(code)
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']

    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")

    # Save the refresh token to the registry for later use
    save_refresh_token_to_registry(refresh_token)

    return access_token, refresh_token

def get_refresh_token_from_registry():
    try:
        # Open the registry key where the refresh token is stored
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\spotipytube\Credentials\CredentialData")
        
        # Retrieve the refresh token value (binary data)
        refresh_token_binary, _ = winreg.QueryValueEx(reg_key, "RefreshToken")
        
        # Close the registry key
        winreg.CloseKey(reg_key)
        
        # Convert the binary data to a string (assuming it was UTF-8 encoded)
        refresh_token = refresh_token_binary.decode('utf-8')
        print(refresh_token)
        return refresh_token
    except Exception as e:
        print(f"Error retrieving refresh token from registry: {e}")
        return None