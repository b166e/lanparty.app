from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import uuid
import asyncio

from routes.admin import router as admin_router
from routes.user import router as user_router
from services.notification_service import admin_connections

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure the imagenes directory exists
os.makedirs("imagenes", exist_ok=True)
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

# Include routers
app.include_router(admin_router)
app.include_router(user_router)

# Handle SSE for admins
@app.get("/sse/admin")
async def sse_admin(request: Request):
    """Server-Sent Events endpoint for admin notifications"""
    client_id = str(uuid.uuid4())
    queue = asyncio.Queue()
    admin_connections[client_id] = queue

    async def event_stream():
        try:
            while True:
                if await request.is_disconnected():
                    break
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            # Clean up when client disconnects
            if client_id in admin_connections:
                del admin_connections[client_id]

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# Create the necessary directories on startup
@app.on_event("startup")
async def startup_event():
    os.makedirs("imagenes", exist_ok=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
