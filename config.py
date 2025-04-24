from typing import Dict
from utils.network import get_local_ip

class Settings:
    """Application settings and configuration"""
    def __init__(self):
        # WiFi credentials for QR code
        self.WIFI_SSID = "RedDelAdmin"
        self.WIFI_PASS = "12345678"
        
        # Get local IP
        self.local_ip = get_local_ip()
        self.SERVER_URL = f"http://{self.local_ip}:8000"
        
        # Admin location
        self.host_coords: Dict[str, float] = {"lat": None, "lon": None}
        
        # Default HTML content
        self.html_por_defecto = "<h1>Bienvenido al sistema</h1>"

# Create settings instance
settings = Settings()
