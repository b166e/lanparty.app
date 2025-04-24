from typing import Dict, Any, Optional, List
import asyncio
import os
import uuid

from models.user import User

# In-memory user storage
usuarios: Dict[str, User] = {}

async def get_user_by_id(user_id: str) -> Optional[User]:
    """Get a user by ID"""
    if not user_id:
        return None
    
    for user in usuarios.values():
        if user.id == user_id:
            return user
    
    return None

async def get_user_by_name(nombre: str) -> Optional[User]:
    """Get a user by name"""
    if not nombre:
        return None
    
    nombre = nombre.strip()
    
    for user in usuarios.values():
        if user.nombre.lower() == nombre.lower():
            return user
    
    return None

async def get_user(identifier: str) -> Optional[User]:
    """Get a user by ID or name"""
    if not identifier:
        return None
    
    # First try to find by ID
    user = await get_user_by_id(identifier)
    if user:
        return user
    
    # If not found, try by name
    return await get_user_by_name(identifier)

async def get_all_users() -> Dict[str, User]:
    """Get all users"""
    return usuarios

async def register_user(nombre: str, data: Dict[str, Any]) -> User:
    """Register a new user or update existing user"""
    if not nombre:
        raise ValueError("Nombre de usuario no puede estar vacío")
        
    nombre = nombre.strip()
    
    # Check if user already exists
    existing_user = await get_user_by_name(nombre)
    
    if existing_user:
        # Update existing user
        for key, value in data.items():
            setattr(existing_user, key, value)
        return existing_user
    else:
        # Create new user
        user_data = {"nombre": nombre, **data}
        new_user = User(**user_data)
        usuarios[new_user.id] = new_user
        return new_user

async def update_user(identifier: str, data: Dict[str, Any]) -> Optional[User]:
    """Update user data by ID or name"""
    if not identifier:
        return None
        
    user = await get_user(identifier)
    
    if user:
        for key, value in data.items():
            setattr(user, key, value)
        return user
    
    return None

async def delete_user(identifier: str) -> bool:
    """Delete a user by ID or name"""
    if not identifier:
        return False
    
    # Try to find by ID first
    for user_id, user in list(usuarios.items()):
        if user.id == identifier or user.nombre.lower() == identifier.lower():
            del usuarios[user_id]
            return True
    
    return False

async def get_users_list() -> List[Dict[str, Any]]:
    """Get a list of users with their data"""
    user_list = []
    
    for user_id, user in usuarios.items():
        user_data = user.to_dict() if hasattr(user, 'to_dict') else {
            "id": user_id,
            "nombre": getattr(user, 'nombre', user_id),
            "lat": getattr(user, 'lat', None),
            "lon": getattr(user, 'lon', None),
            "html": getattr(user, 'html', None),
            "pantalla": getattr(user, 'pantalla', None),
            "pos_x": getattr(user, 'pos_x', None),
            "pos_y": getattr(user, 'pos_y', None)
        }
        user_list.append(user_data)
    
    return user_list
