from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from connection_manager import manager
from routes.user import router as user_router
from routes.admin import router as admin_router

app = FastAPI()

# Carpeta de assets (CSS, JS, imágenes estáticas)
app.mount("/static", StaticFiles(directory="static"), name="static")
# Carpeta donde guardas y sirves los recortes y el fondo dinámico
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

# Routers
app.include_router(user_router)
app.include_router(admin_router)

@app.websocket("/ws/user/{user_id}")
async def websocket_user(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)