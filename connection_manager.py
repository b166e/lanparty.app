# connection_manager.py
from typing import Dict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # mapea user_id → WebSocket
        self.active: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active[user_id] = websocket

    def disconnect(self, user_id: str):
        self.active.pop(user_id, None)

    async def send_personal_message(self, message: dict, user_id: str):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        for ws in list(self.active.values()):
            await ws.send_json(message)

# instancia global para usar desde main y desde routes/admin
manager = ConnectionManager()
