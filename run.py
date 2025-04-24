import os
import subprocess
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import jinja2
        import aiofiles
        from PIL import Image
        import qrcode
        return True
    except ImportError as e:
        print(f"Dependencia faltante: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("Instalando dependencias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencias instaladas correctamente.")

def create_directories():
    """Create necessary directories"""
    os.makedirs("imagenes", exist_ok=True)
    print("Directorios creados.")

def run_app():
    """Run the FastAPI application"""
    print("Iniciando la aplicación...")
    subprocess.call([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"])

if __name__ == "__main__":
    print("Verificando entorno...")
    
    if not check_dependencies():
        install_dependencies()
    
    create_directories()
    run_app()
