import socket

def get_local_ip() -> str:
    """
    Get the local IP address of the machine.
    """
    # Create a socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # Connect to Google DNS (doesn't actually send data)
        s.connect(("8.8.8.8", 80))
        
        # Get the local IP address associated with the connection
        local_ip = s.getsockname()[0]
        
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "127.0.0.1"  # Fallback to localhost
    finally:
        s.close()
