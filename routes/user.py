from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uuid
import asyncio
import time

from services.user_service import register_user, update_user, get_user, get_user_by_name
from services.notification_service import notify_admins, user_connections
from utils.qr import generar_qr
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with registration form"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/registrar")
async def registrar(request: Request):
    """Register a new user with geolocation"""
    data = await request.json()
    nombre = data["nombre"].strip()
    
    # Create or update user
    user = await register_user(nombre, {
        "lat": data.get("lat"),
        "lon": data.get("lon"),
        "html": None
    })
    
    # Notify admins of new registration
    await notify_admins()
    
    return {"status": "ok", "user_id": user.id}

@router.post("/pantalla")
async def recibir_tamanio(request: Request):
    """Receive screen dimensions from user"""
    data = await request.json()
    identifier = data.get("nombre")
    
    if identifier:
        # Update user's screen dimensions
        await update_user(identifier, {
            "pantalla": {
                "ancho": data.get("ancho"),
                "alto": data.get("alto")
            }
        })
    
    return {"status": "ok"}

@router.get("/ver-html/{identifier}", response_class=HTMLResponse)
async def ver_html(request: Request, identifier: str):
    """Display HTML content for a specific user"""
    user = await get_user(identifier)
    
    if not user:
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>Usuario no encontrado</p>
                <p><a href="/">Volver a la página principal</a></p>
            </body>
        </html>
        """)
    
    # Get user's HTML content or use default
    html_content = user.html if user and user.html else settings.html_por_defecto
    
    # Generate QR code for this user's page
    qr_code = generar_qr(f"{settings.SERVER_URL}/ver-html/{user.id}")
    
    # Generate timestamp to avoid image caching
    timestamp = int(time.time())
    
    return templates.TemplateResponse(
        "user_view.html", 
        {
            "request": request, 
            "nombre": user.nombre,
            "user_id": user.id,
            "html_content": html_content,
            "qr_code": qr_code,
            "timestamp": timestamp
        }
    )

@router.get("/sse/usuario/{identifier}")
async def sse_usuario(request: Request, identifier: str):
    """Server-Sent Events endpoint for user notifications"""
    client_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    
    user = await get_user(identifier)
    if not user:
        return StreamingResponse(content=[], media_type="text/event-stream")
    
    user_connections[client_id] = {"queue": queue, "nombre": user.nombre, "id": user.id}

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            # Clean up when client disconnects
            if client_id in user_connections:
                del user_connections[client_id]

    return StreamingResponse(event_stream(), media_type="text/event-stream")
