from django.contrib import messages
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64
import winreg
import base64


# Encryption and decryption functions
def encrypt(data, key, iv):
    """Encrypt the data using AES."""
    try:
        data = data.encode("utf-8")
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Add padding to the data
        padding_length = 16 - (len(data) % 16)
        padded_data = data + bytes([padding_length] * padding_length)

        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(encrypted_data).decode("utf-8")
    except Exception as e:
        print(f"Encryption failed: {e}")
        return None


def decrypt(encrypted_data, key, iv):
    """
    Decrypt the data using AES in CBC mode with PKCS7 padding.
    
    Args:
        encrypted_data (str): The Base64-encoded encrypted string.
        key (bytes): The AES key (must be 16, 24, or 32 bytes).
        iv (bytes): The AES initialization vector (must be 16 bytes).
    
    Returns:
        str: The decrypted plaintext string, or None if decryption fails.
    """
    try:
        # Decode the Base64-encoded string
        encrypted_bytes = base64.b64decode(encrypted_data)
        
        # Ensure the key and IV are of the correct length
        if len(key) not in [16, 24, 32]:
            raise ValueError("The key must be 16, 24, or 32 bytes long.")
        if len(iv) != 16:
            raise ValueError("The IV must be 16 bytes long.")

        # Set up AES decryption
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt the data
        decrypted_bytes = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # Remove PKCS7 padding
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        unpadded_data = unpadder.update(decrypted_bytes) + unpadder.finalize()

        # Return the plaintext as a string
        return unpadded_data.decode('utf-8')
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None


def get_from_registry(path, key_name):
    """Retrieve data from the registry."""
    try:
        reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
        encrypted_data, reg_type = winreg.QueryValueEx(reg_key, key_name)
        winreg.CloseKey(reg_key)
        if reg_type == winreg.REG_BINARY:
            return encrypted_data
    except Exception as e:
        print(f"Error retrieving from registry: {e}")
        return None


key = get_from_registry(r"SOFTWARE\Spotipytube", "EncryptionKey")
iv = get_from_registry(r"SOFTWARE\Spotipytube", "EncryptionIV")

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