from typing import Dict, Optional, List
from pydantic import BaseModel, Field
import uuid

class ScreenInfo(BaseModel):
    ancho: int
    alto: int

class UserPosition(BaseModel):
    pos_x: int
    pos_y: int

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nombre: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    html: Optional[str] = None
    pantalla: Optional[ScreenInfo] = None
    pos_x: Optional[int] = None
    pos_y: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "lat": self.lat,
            "lon": self.lon,
            "html": self.html,
            "pantalla": self.pantalla.dict() if self.pantalla else None,
            "pos_x": self.pos_x,
            "pos_y": self.pos_y
        }
