# utils/scaling.py
from math import floor, ceil
from typing import List, Dict, Optional


class ScalingManager:
    def __init__(
        self,
        background_width_px: int = 1000,
        background_height_px: int = None,
        background_width_cm: float = 500,
        scale_factor: float = 1.0
    ):
        self.background_width_px = background_width_px
        self.background_height_px = background_height_px or background_width_px
        self.background_width_cm = background_width_cm
        self.scale_factor = scale_factor
        self.container_width_px = None
        self.px_per_cm = background_width_px / background_width_cm

    def update_background_dimensions(
        self,
        width_px: int,
        height_px: int = None,
        width_cm: float = None,
        container_width: int = None
    ):
        self.background_width_px = width_px
        if height_px is not None:
            self.background_height_px = height_px
        if width_cm is not None:
            self.background_width_cm = width_cm
        if container_width is not None:
            self.container_width_px = container_width
        self.px_per_cm = self.background_width_px / self.background_width_cm
        print(f"ScalingManager actualizado: {width_px}×{height_px} px, {width_cm} cm, contenedor: {container_width} px")

    def screen_px_to_cm(self, px: float, dpi: float = 96) -> float:
        return (px / dpi) * 2.54

    def cm_to_canvas_px(self, cm: float) -> float:
        return cm * self.px_per_cm * self.scale_factor

    def calculate_screen_dimensions(
        self,
        screen_width_px: int,
        screen_height_px: int,
      #  dpi: float = None
      dpi = 96  # fijo para depuración
    ) -> dict:
        if dpi is None:
            if screen_width_px < 800:
                dpi = 300
            elif screen_width_px < 1500:
                dpi = 120
            else:
                dpi = 96
        width_cm  = self.screen_px_to_cm(screen_width_px, dpi)
        height_cm = self.screen_px_to_cm(screen_height_px, dpi)
        return {
            'width_px': screen_width_px,
            'height_px': screen_height_px,
            'width_cm': width_cm,
            'height_cm': height_cm,
            'canvas_width': self.cm_to_canvas_px(width_cm),
            'canvas_height': self.cm_to_canvas_px(height_cm),
            'dpi': dpi
        }

    def calculate_optimal_scale_factor(self, screen_dimensions: list, container_width: int) -> float:
        if not screen_dimensions:
            return 1.0
        total_width_cm    = max(d['width_cm'] * 1.2 for d in screen_dimensions)
        px_per_cm_needed  = container_width / total_width_cm
        optimal_scale     = px_per_cm_needed / self.px_per_cm
        return max(0.1, min(2.0, optimal_scale))

    def calculate_crop_box(
        self,
        pos: tuple,
        canvas_size: tuple,
        image_size: tuple
    ) -> tuple:
        """
        pos:  (x, y)      -- coordenadas dentro del div preview
        canvas_size: (w, h) en px en preview
        image_size:  (w, h) en px originales
        """
        if self.container_width_px is None:
            raise ValueError("container_width_px no inicializado")

        # Factor al que la imagen se escala en el DOM:
        scale_ui = self.container_width_px / self.background_width_px

        x_orig = pos[0] / scale_ui
        y_orig = pos[1] / scale_ui
        w_orig = canvas_size[0] / scale_ui
        h_orig = canvas_size[1] / scale_ui

        x1 = int(floor(x_orig))
        y1 = int(floor(y_orig))
        x2 = int(ceil(x_orig + w_orig))
        y2 = int(ceil(y_orig + h_orig))

        return (x1, y1, x2, y2)

    def validate_crop_box(self, box: tuple, image_width: int, image_height: int) -> tuple:
        if not box:
            return None
        left, top, right, bottom = box
        left   = max(0, min(left,   image_width  - 1))
        top    = max(0, min(top,    image_height - 1))
        right  = max(left + 1,  min(right,  image_width))
        bottom = max(top  + 1,  min(bottom, image_height))
        if right - left < 10 or bottom - top < 10:
            print(f"Caja de recorte demasiado pequeña: {(left, top, right, bottom)}")
            return None
        return (left, top, right, bottom)

    def adjust_for_aspect_ratio(self, box: tuple, target_w: int, target_h: int) -> tuple:
        if not box:
            return None
        left, top, right, bottom = box
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0 or target_w <= 0 or target_h <= 0:
            return box
        current_ratio = w / h
        target_ratio  = target_w / target_h
        if abs(current_ratio - target_ratio) < 0.01:
            return box
        if current_ratio > target_ratio:
            new_w    = int(h * target_ratio)
            cx       = (left + right) // 2
            left     = cx - new_w // 2
            right    = left + new_w
        else:
            new_h    = int(w / target_ratio)
            cy       = (top + bottom) // 2
            top      = cy - new_h // 2
            bottom   = top + new_h
        return (left, top, right, bottom)

    def get_px_per_cm(self) -> float:
        return self.px_per_cm
    def get_auto_zoom_for_all_users(self, users: List[dict], margin_percent: float = 0.95) -> float:
        """
        Calcula un factor de zoom basado en el bounding box de todos los usuarios dentro del canvas.
        Considera el espacio disponible (background) y aplica un margen opcional.
        """
        if not users:
            return 1.0

        min_x = min(u['pos_x'] for u in users)
        min_y = min(u['pos_y'] for u in users)
        max_x = max(u['pos_x'] + u['canvas_width'] for u in users)
        max_y = max(u['pos_y'] + u['canvas_height'] for u in users)

        total_width = max_x - min_x
        total_height = max_y - min_y

        max_display_width = self.background_width_px * margin_percent
        max_display_height = self.background_height_px * margin_percent

        zoom_x = max_display_width / total_width if total_width else 1.0
        zoom_y = max_display_height / total_height if total_height else 1.0

        zoom = min(zoom_x, zoom_y)
        return round(max(0.1, min(zoom, 3.0)), 2)



    def calculate_auto_positions(self, users: List[dict], container_width: int, padding: int = 10) -> List[dict]:
        """
        Distribuye automáticamente las pantallas en filas ajustadas al ancho del canvas.
        """
        x, y = padding, padding
        max_row_height = 0
        layouted = []

        for u in users:
            w = u["canvas_width"]
            h = u["canvas_height"]

            if x + w + padding > container_width:
                # Nueva fila
                x = padding
                y += max_row_height + padding
                max_row_height = 0

            layouted.append({
                **u,
                "pos_x": int(x),
                "pos_y": int(y)
            })

            x += w + padding
            max_row_height = max(max_row_height, h)

        return layouted