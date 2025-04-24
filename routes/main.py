# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routes.user import router as user_router
from routes.admin import router as admin_router

app = FastAPI()

# 1) Sirve /static (tu JS y CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2) Incluye el router de usuario (registro "/" + SSE + pantalla + ver-html)
app.include_router(user_router)

# 3) Incluye el router admin (panel /admin, /qr, /admin/preview…)
app.include_router(admin_router, prefix="")  
# — o con prefix="/admin" si prefieres: ahora todas las rutas de admin tienen /admin delante
