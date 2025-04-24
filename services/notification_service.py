from typing import Dict
import asyncio

# Connection storage
admin_connections: Dict[str, asyncio.Queue] = {}
user_connections: Dict[str, Dict] = {}

async def notify_admins() -> None:
    """Notify all connected admin clients to reload"""
    for queue in admin_connections.values():
        await queue.put("recargar")

async def notify_user_by_name(nombre: str) -> None:
    """Notify a specific user to reload"""
    nombre = nombre.strip()
    
    for conn in user_connections.values():
        if conn["nombre"] == nombre:
            await conn["queue"].put("recargar")

async def notify_users_with_default() -> None:
    """Notify all users who are using the default HTML to reload"""
    from services.user_service import usuarios
    
    for conn in user_connections.values():
        nombre = conn["nombre"]
        if nombre in usuarios and not usuarios[nombre].get("html"):
            await conn["queue"].put("recargar")
