from fastapi import APIRouter, Request, Form, File, UploadFile, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import os
import aiofiles
import time
from typing import Dict, List
from PIL import Image
from connection_manager import manager


from models.user import ScreenInfo, User
from utils.qr import generar_qr
from utils.geo import calcular_distancia
from utils.scaling import ScalingManager
from services.user_service import (
    get_all_users,
    get_user,
    update_user,
    delete_user,
    get_users_list
)
from services.notification_service import (
    notify_admins,
    notify_user_by_name,
    notify_users_with_default
)
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Expose Jinja2 helpers
templates.env.globals.update({
    "max": max,
    "min": min,
    "int": int,
    "float": float,
    "round": round,
    "calcular_distancia": calcular_distancia
})

# Single scaling manager instance
scaling_manager = ScalingManager(
    background_width_px=1000,
    background_width_cm=500,
    scale_factor=1.0
)


from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import time
from typing import Dict
from models.user import ScreenInfo, User
from utils.geo import calcular_distancia
from utils.qr import generar_qr
from services.user_service import get_all_users
from config import settings

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    try:
        # 1) Timestamp ANTES del loop
        timestamp = int(time.time())

        # Tus QR globales
        qr_wifi = generar_qr(f"WIFI:S:{settings.WIFI_SSID};T:WPA;P:{settings.WIFI_PASS};;")
        qr_link = generar_qr(f"{settings.SERVER_URL}/")

        users = await get_all_users() or {}
        usuarios: Dict[str, dict] = {}

        for u in users.values():
            # normalizas la pantalla, etc...
            # ...
            usuarios[u.id] = {
                "id": u.id,
                "nombre": u.nombre,
                # resto de campos...
                # 2) QR individual con timestamp anti-cache
                "qr_url": f"/qr/{u.id}?t={timestamp}"
            }

        return templates.TemplateResponse("admin.html", {
            "request": request,
            "qr_wifi": qr_wifi,
            "qr_link": qr_link,
            "usuarios": usuarios,
            "html_por_defecto": settings.html_por_defecto,
            "host_coords": settings.host_coords,
            "timestamp": timestamp
        })

    except Exception as e:
        print(f"Error en /admin: {e}")
        return HTMLResponse(
            status_code=500,
            content=f"<h1>Error en administración</h1><p>{e}</p>"
        )

@router.get("/qr/{identifier}")
async def get_user_qr(identifier: str):
    """Generate QR code for a specific user"""
    try:
        u = await get_user(identifier)
        if not u:
            return Response(status_code=404, content="Usuario no encontrado")
        qr = generar_qr(f"{settings.SERVER_URL}/ver-html/{u.id}")
        return Response(content=qr.split(",")[1], media_type="image/png")
    except Exception as e:
        print(f"Error generating QR: {e}")
        return Response(status_code=500)
    
    
@router.get("/admin/preview", response_class=HTMLResponse)
async def admin_preview(request: Request):
    """Screen layout preview page"""
    try:
        users: Dict[str, User] = await get_all_users()
        bg_path = "imagenes/fondo.jpg"
        bg_info = {"exists": False, "width": 1000, "height": 600}
        container_w = 1000

        # Load background and update scaling
        if os.path.exists(bg_path):
            with Image.open(bg_path) as img:
                w, h = img.size
            scaling_manager.update_background_dimensions(w, h, width_cm=1000, container_width=container_w)
            max_h = 1200
            if h > max_h:
                scale = max_h / h
                bg_info = {"exists": True, "width": w, "height": h,
                           "adjusted_width": w * scale, "adjusted_height": max_h}
            else:
                bg_info = {"exists": True, "width": w, "height": h}

        proc_users: Dict[str, dict] = {}
        dims_list: List[dict] = []

        for u in users.values():
            p = u.pantalla
            if isinstance(p, ScreenInfo):
                w_px, h_px = p.ancho, p.alto
            elif isinstance(p, dict):
                w_px, h_px = p.get("ancho", 100), p.get("alto", 100)
            else:
                w_px, h_px = 100, 100

            dims = scaling_manager.calculate_screen_dimensions(w_px, h_px)
            dims_list.append(dims)

            # Convertir posiciones relativas a píxeles
            pos_x_percent = getattr(u, 'pos_x_percent', 0) or 0
            pos_y_percent = getattr(u, 'pos_y_percent', 0) or 0
            pos_x_px = (pos_x_percent / 100) * bg_info['width']
            pos_y_px = (pos_y_percent / 100) * bg_info['height']

            proc_users[u.id] = {
                "id": u.id,
                "nombre": u.nombre,
                "lat": u.lat,
                "lon": u.lon,
                "html": u.html,
                "pantalla": {"ancho": w_px, "alto": h_px},
                "ancho_px": w_px,
                "alto_px": h_px,
                **dims,
                "pos_x": pos_x_px,
                "pos_y": pos_y_px,
                "pos_x_percent": pos_x_percent,
                "pos_y_percent": pos_y_percent
            }

        opt = scaling_manager.calculate_optimal_scale_factor(dims_list, container_w)
        scaling_manager.scale_factor = opt

        for v in proc_users.values():
            new = scaling_manager.calculate_screen_dimensions(v['ancho_px'], v['alto_px'])
            v.update({
                "canvas_width": new['canvas_width'],
                "canvas_height": new['canvas_height']
            })

        # Asegurar valores válidos
        for v in proc_users.values():
            v["pos_x"] = v.get("pos_x") or 0
            v["pos_y"] = v.get("pos_y") or 0
            v["canvas_width"] = v.get("canvas_width") or 1
            v["canvas_height"] = v.get("canvas_height") or 1

        ts = int(time.time())
        zoom_ui = scaling_manager.get_auto_zoom_for_all_users(list(proc_users.values()))

        for v in proc_users.values():
            new = scaling_manager.calculate_screen_dimensions(v['ancho_px'], v['alto_px'])
            v.update({
                "canvas_width": new['canvas_width'],
                "canvas_height": new['canvas_height'],
                "recorte_url": f"/imagenes/{v['id']}.jpg?t={ts}",
                "qr_url": f"/qr/{v['id']}"
            })

        init_h = min(bg_info.get('height', 600) * scaling_manager.scale_factor, 800)

        return templates.TemplateResponse("preview.html", {
            "request": request,
            "usuarios": proc_users,
            "background": bg_info,
            "scale_factor": scaling_manager.scale_factor,
            "optimal_scale": opt,
            "background_width_cm": scaling_manager.background_width_cm,
            "timestamp": ts,
            "initial_height": init_h,
            "container_width": container_w,
            "px_por_cm": scaling_manager.get_px_per_cm(),
            "zoom_ui": zoom_ui
        })

    except Exception as e:
        print(f"Error en /admin/preview: {e}")
        return HTMLResponse(status_code=500, content=f"<h1>Error en simulación</h1><p>{e}</p>")



@router.post("/enviar-html")
async def enviar_html(identifier: str = Form(...), html: str = Form(...)):
    """Update HTML content for a specific user"""
    try:
        user = await update_user(identifier, {"html": html})
        if not user:
            return HTMLResponse(status_code=404, content="<h1>Usuario no encontrado</h1>")
        await notify_user_by_name(user.nombre)
        await notify_admins()
        return HTMLResponse("<script>window.location='/admin';</script>")
    except Exception as e:
        print(f"Error in /enviar-html: {e}")
        return HTMLResponse(status_code=500, content=f"<h1>Error al enviar HTML</h1><p>{e}</p>")


@router.post("/html-por-defecto")
async def actualizar_html_por_defecto(html: str = Form(...)):
    """Update default HTML content"""
    try:
        settings.html_por_defecto = html
        await notify_users_with_default()
        await notify_admins()
        return HTMLResponse("<script>window.location='/admin';</script>")
    except Exception as e:
        print(f"Error in /html-por-defecto: {e}")
        return HTMLResponse(status_code=500, content=f"<h1>Error al actualizar HTML por defecto</h1><p>{e}</p>")


@router.post("/host")
async def update_host(request: Request):
    """Update admin's location"""
    try:
        data = await request.json()
        settings.host_coords["lat"] = data["lat"]
        settings.host_coords["lon"] = data["lon"]
        await notify_admins()
        return {"status": "admin location updated"}
    except Exception as e:
        print(f"Error in /host: {e}")
        return {"status": "error", "mensaje": str(e)}


@router.post("/upload-background")
async def upload_background(file: UploadFile = File(...), container_width: int = Form(1000)):
    """Upload and save background image for preview"""
    try:
        os.makedirs("imagenes", exist_ok=True)
        async with aiofiles.open("imagenes/fondo.jpg", "wb") as out_file:
            await out_file.write(await file.read())
        with Image.open("imagenes/fondo.jpg") as img:
            scaling_manager.update_background_dimensions(
                width_px=img.width,
                height_px=img.height,
                container_width=container_width
            )
        return {"status": "ok", "mensaje": "Imagen de fondo actualizada"}
    except Exception as e:
        print(f"Error in upload-background: {e}")
        return {"status": "error", "mensaje": str(e)}

@router.post("/save-positions")
async def save_positions(request: Request):
    data = await request.json()
    positions = data.get("positions", {})
    
    # Obtener tamaño actual del canvas para normalizar las posiciones
    canvas_width = data.get("canvas_width", 1000)
    canvas_height = data.get("canvas_height", 600)

    # Validación de fondo para tomar medidas reales si no se envían
    if os.path.exists("imagenes/fondo.jpg"):
        with Image.open("imagenes/fondo.jpg") as img:
            canvas_width = img.width
            canvas_height = img.height

    for identifier, coords in positions.items():
        if isinstance(coords, dict):
            # Normalizamos las posiciones si es necesario
            pos_x_px = coords.get("pos_x", 0)
            pos_y_px = coords.get("pos_y", 0)
            
            pos_x_pct = round(pos_x_px / canvas_width, 6)
            pos_y_pct = round(pos_y_px / canvas_height, 6)
            
            await update_user(identifier, {"pos_x": pos_x_pct, "pos_y": pos_y_pct})

    return {"status": "ok", "mensaje": "Posiciones guardadas como porcentaje"}

@router.post("/update-container-width")
async def update_container_width(request: Request):
    """Update the container width for scaling calculations"""
    try:
        data = await request.json()
        cw = data.get("width", 1000)
        if os.path.exists("imagenes/fondo.jpg"):
            with Image.open("imagenes/fondo.jpg") as img:
                scaling_manager.update_background_dimensions(img.width, img.height, cw)
        return {"status": "ok", "mensaje": "Container width updated"}
    except Exception as e:
        print(f"Error in update-container-width: {e}")
        return {"status": "error", "mensaje": str(e)}


@router.get("/test-crop/{user_id}")
async def test_crop(
    user_id: str,
    container_width: int = Query(1000),
    fit_to_width: bool = Query(True)
):
    """Test crop calculation for a single user"""
    try:
        path = "imagenes/fondo.jpg"
        if not os.path.exists(path):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "mensaje": "Imagen fondo.jpg no encontrada"}
            )

        with Image.open(path) as img:
            scaling_manager.update_background_dimensions(
                width_px=img.width,
                height_px=img.height,
                container_width=container_width
            )

            u = await get_user(user_id)
            if not u:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "mensaje": "Usuario no encontrado"}
                )

            # Obtener dimensiones físicas del usuario
            p = u.pantalla
            screen = ScreenInfo(**p) if isinstance(p, dict) else p
            w_px, h_px = screen.ancho, screen.alto
            dims = scaling_manager.calculate_screen_dimensions(w_px, h_px)
            canvas_size = (dims['canvas_width'], dims['canvas_height'])
            pos = (u.pos_x or 0, u.pos_y or 0)

            # 🔁 Desescalado desde canvas a imagen real
            descaled_pos = (
                int(pos[0] / scaling_manager.scale_factor),
                int(pos[1] / scaling_manager.scale_factor)
            )
            descaled_canvas_size = (
                int(canvas_size[0] / scaling_manager.scale_factor),
                int(canvas_size[1] / scaling_manager.scale_factor)
            )

            box = scaling_manager.calculate_crop_box(
                descaled_pos,
                descaled_canvas_size,
                (img.width, img.height)
            )

            box = scaling_manager.validate_crop_box(box, img.width, img.height)
            if box:
                box = scaling_manager.adjust_for_aspect_ratio(box, w_px, h_px)
                box = scaling_manager.validate_crop_box(box, img.width, img.height)

            return {
                "usuario": u.nombre,
                "id": u.id,
                "pantalla": f"{w_px}x{h_px} px",
                "posicion": f"{pos}",
                "dimensiones_fisicas": f"{dims['width_cm']:.1f}x{dims['height_cm']:.1f} cm",
                "dimensiones_canvas": f"{canvas_size[0]:.1f}x{canvas_size[1]:.1f} px",
                "factor_escala": scaling_manager.scale_factor,
                "px_por_cm": scaling_manager.px_per_cm,
                "caja_recorte": box or "Inválida",
                "imagen_fondo": f"{img.width}x{img.height} px",
                "ajuste_ancho": fit_to_width,
                "container_width": container_width
            }

    except Exception as e:
        print(f"Error in test-crop: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "mensaje": str(e)})


@router.get("/generar-recortes")
async def generar_recortes(container_width: int = Query(1000)):
    path = "imagenes/fondo.jpg"
    with Image.open(path) as img:
        # vuelves a inicializar la escala con el mismo container_width:
        scaling_manager.update_background_dimensions(
            width_px=img.width, height_px=img.height,
            container_width=container_width
        )

        users = await get_all_users()
        for u in users.values():
            # dimensiones pantalla en px
            w_px, h_px = u.pantalla["ancho"], u.pantalla["alto"]
            # calculas canvas dims con la misma lógica
            dims = scaling_manager.calculate_screen_dimensions(w_px, h_px)
            canvas_w, canvas_h = dims["canvas_width"], dims["canvas_height"]

            # obtenemos la posición CSS px que guardamos
            x_css, y_css = u.pos_x or 0, u.pos_y or 0

            # ➡️ transformamos de CSS px a posición en la imagen real
            #    usando la proporción real_px / css_px
            real_x = int(x_css * (img.width  / container_width))
            real_y = int(y_css * (img.height / container_width))

            # ajustamos canvas dims a reales también
            real_w = int(canvas_w * (img.width  / container_width))
            real_h = int(canvas_h * (img.height / container_width))

            box = scaling_manager.calculate_crop_box(
                (real_x, real_y),
                (real_w, real_h),
                (img.width, img.height)
            )
            box = scaling_manager.validate_crop_box(box, img.width, img.height)
            if not box:
                continue
            box = scaling_manager.adjust_for_aspect_ratio(box, w_px, h_px)
            box = scaling_manager.validate_crop_box(box, img.width, img.height)
            if not box:
                continue

            crop = img.crop(box)
            if crop.size != (w_px, h_px):
                crop = crop.resize((w_px, h_px), Image.LANCZOS)
            crop.save(f"imagenes/{u.id}.jpg", quality=95)
    return {"status": "ok"}

@router.get("/api/users")
async def get_users():
    """API endpoint to get all users with distances"""
    try:
        users = await get_users_list()
        enriched = []
        for u in users:
            dist = calcular_distancia(settings.host_coords.get("lat"), settings.host_coords.get("lon"), u.lat, u.lon)
            enriched.append({
                "id": u.id,
                "nombre": u.nombre,
                "lat": u.lat,
                "lon": u.lon,
                "distancia": dist,
                "pantalla": u.pantalla,
                "html": u.html
            })
        enriched.sort(key=lambda x: x["nombre"])
        return enriched
    except Exception as e:
        print(f"Error in /api/users: {e}")
        return JSONResponse(status_code=500, content={"status":"error","mensaje":str(e)})


@router.delete("/eliminar-usuario/{identifier}")
async def eliminar_usuario(identifier: str):
    """Delete a user by ID or name"""
    try:
        result = await delete_user(identifier)
        if result:
            img_path = f"imagenes/{identifier}.jpg"
            if os.path.exists(img_path):
                os.remove(img_path)
            await notify_admins()
            return {"status": "ok", "mensaje": "Usuario eliminado correctamente"}
        return {"status": "error", "mensaje": "Usuario no encontrado"}
    except Exception as e:
        print(f"Error in eliminar-usuario: {e}")
        return JSONResponse(status_code=500, content={"status":"error","mensaje":str(e)})
    
@router.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "fondo":
                await manager.broadcast(data)
            elif (uid := data.get("user_id")):
                await manager.send_personal_message(data, uid)
    except WebSocketDisconnect:
        pass