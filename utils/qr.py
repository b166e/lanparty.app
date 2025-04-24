import qrcode
import base64
from io import BytesIO

def generar_qr(data: str) -> str:
    """
    Generate a QR code for the given data and return as a base64 encoded string.
    """
    # Create QR code instance
    img = qrcode.make(data)
    
    # Save to buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    
    # Encode to base64 string
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    # Return as data URL
    return f"data:image/png;base64,{img_str}"
