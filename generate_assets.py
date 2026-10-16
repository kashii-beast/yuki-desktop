import os
import math
import glob
from PIL import Image, ImageDraw
from src.config import PET_SIZE

# Рисуем в 4 раза крупнее (512x512) для идеального сглаживания (Supersampling)
SCALE = 4
CANVAS_SIZE = 128 * SCALE
FRAMES_PER_STATE = 8

# Палитра Юки
OUTLINE_COLOR = "#3A3F58"     # Стильная светло-индиговая обводка (чтобы черный кот читался на темных обоях)
FUR_COLOR = "#14161F"         # Глубокий угольно-черный мех
FUR_HIGHLIGHT = "#25293A"     # Блик на макушке
EAR_INNER = "#FF6B8B"         # Розовые ушки внутри
SCLERA_COLOR = "#FFFFFF"      # Белок глаза
IRIS_NORMAL = "#00F5D4"       # Неоново-бирюзовая радужка
IRIS_SHOCK = "#FF2A85"        # Ярко-розовая радужка при удивлении/полете
PUPIL_COLOR = "#0B0C10"       # Зрачок
ZZZ_COLOR = "#72EFDD"         # Цвет буковок Zzz во сне


def draw_z(draw: ImageDraw.ImageDraw, x: float, y: float, size: float, color: str):
    """Рисует стильную буковку Z для анимации сна."""
    w = max(2, int(size // 4))
    draw.line([(x, y), (x + size, y), (x, y + size), (x + size, y + size)], fill=color, width=w, joint="curve")


def create_frame(filename: str, state: str, frame_idx: int):
    img = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Фаза от 0 до 2*PI для бесшовной плавной анимации
    phase = (frame_idx / FRAMES_PER_STATE) * (2 * math.pi)
    sin_val = math.sin(phase)
    cos_val = math.cos(phase)

    cx = CANVAS_SIZE // 2
    floor_y = 112 * SCALE

    # --- 1. Тень под котом (на земле) ---
    if state not in ("falling", "dragged"):
        shadow_rx = (34 if state != "sleep" else 42) * SCALE + int(sin_val * 2 * SCALE)
        draw.ellipse(
            [cx - shadow_rx, floor_y - 6 * SCALE, cx + shadow_rx, floor_y + 4 * SCALE],
            fill=(0, 0, 0, 90)
        )

    # --- 2. Расчет физики тела по состояниям ---
    bob_y = int(sin_val * 3 * SCALE)
    tilt_x = 0
    body_rx = 32 * SCALE
    body_ry = 28 * SCALE
    base_y = 78 * SCALE + bob_y

    if state == "walk_left":
        tilt_x = -4 * SCALE
        bob_y = int(abs(sin_val) * -5 * SCALE)
        base_y = 78 * SCALE + bob_y
    elif state == "walk_right":
        tilt_x = 4 * SCALE
        bob_y = int(abs(sin_val) * -5 * SCALE)
        base_y = 78 * SCALE + bob_y
    elif state == "sleep":
        # Сплющиваемся в уютный пушистый клубочек на полу
        body_rx = 38 * SCALE + int(sin_val * 1.5 * SCALE)
        body_ry = 21 * SCALE - int(sin_val * 1.5 * SCALE)
        base_y = 89 * SCALE
    elif state == "dragged":
        tilt_x = int(sin_val * 5 * SCALE)
        body_rx = 26 * SCALE
        body_ry = 36 * SCALE
        base_y = 68 * SCALE
    elif state == "falling":
        body_rx = 25 * SCALE
        body_ry = 35 * SCALE
        base_y = 64 * SCALE + int(sin_val * 2 * SCALE)

    bx = cx + tilt_x
    by = base_y

    # --- 3. Пушистый виляющий хвост ---
    tail_points = []
    tail_dir = 1 if state != "walk_right" else -1
    for t in range(10):
        ratio = t / 9.0
        tx = bx + tail_dir * int((body_rx * 0.7) + ratio * 22 * SCALE)
        ty = by + int(body_ry * 0.3) - int(ratio * 28 * SCALE) + int(math.sin(phase + ratio * 3) * 6 * SCALE)
        tail_points.append((tx, ty))

    if state != "sleep":
        draw.line(tail_points, fill=OUTLINE_COLOR, width=11 * SCALE, joint="curve")
        draw.line(tail_points, fill=FUR_COLOR, width=7 * SCALE, joint="curve")

    # --- 4. Ушки (с розовой серединкой и обводкой) ---
    ear_y_top = by - body_ry - (14 * SCALE if state != "sleep" else 6 * SCALE)
    ear_w = 18 * SCALE

    for side in (-1, 1):
        # Внешний контур уха
        outer_ear = [
            (bx + side * int(body_rx * 0.75), by - int(body_ry * 0.4)),
            (bx + side * int(body_rx * 0.55) + int(sin_val * 2 * SCALE), ear_y_top),
            (bx + side * int(body_rx * 0.15), by - int(body_ry * 0.85)),
        ]
        draw.polygon(outer_ear, fill=FUR_COLOR, outline=OUTLINE_COLOR, width=3 * SCALE)

        # Розовая внутренняя часть уха
        inner_ear = [
            (bx + side * int(body_rx * 0.65), by - int(body_ry * 0.5)),
            (bx + side * int(body_rx * 0.53) + int(sin_val * 2 * SCALE), ear_y_top + 6 * SCALE),
            (bx + side * int(body_rx * 0.25), by - int(body_ry * 0.8)),
        ]
        draw.polygon(inner_ear, fill=EAR_INNER)

    # --- 5. Туловище с мягкой обводкой и бликом на макушке ---
    draw.ellipse(
        [bx - body_rx, by - body_ry, bx + body_rx, by + body_ry],
        fill=FUR_COLOR, outline=OUTLINE_COLOR, width=3 * SCALE
    )
    # Блик на шерстке сверху
    draw.arc(
        [bx - int(body_rx * 0.7), by - int(body_ry * 0.85), bx + int(body_rx * 0.7), by],
        start=200, end=340, fill=FUR_HIGHLIGHT, width=2 * SCALE
    )

    # --- 6. Лапки ---
    paw_y = by + body_ry - 2 * SCALE
    for side in (-1, 1):
        paw_x = bx + side * 14 * SCALE
        paw_offset_y = 0
        if state in ("walk_left", "walk_right"):
            # Перебираем лапками в противофазе
            paw_offset_y = int(math.sin(phase + (0 if side == -1 else math.pi)) * 5 * SCALE)
        elif state in ("dragged", "falling"):
            # Болтаем лапками в воздухе
            paw_offset_y = 5 * SCALE + int(sin_val * side * 4 * SCALE)

        py = paw_y + paw_offset_y
        draw.ellipse(
            [paw_x - 7 * SCALE, py - 5 * SCALE, paw_x + 7 * SCALE, py + 5 * SCALE],
            fill=FUR_COLOR, outline=OUTLINE_COLOR, width=2 * SCALE
        )

    # --- 7. ОГРОМНЫЙ ГЛАЗ ЦИКЛОПА ---
    eye_cx = bx + (6 * SCALE if state == "walk_right" else (-6 * SCALE if state == "walk_left" else 0))
    eye_cy = by - int(body_ry * 0.15)
    eye_r = 14 * SCALE

    if state == "sleep":
        # Закрытый сонный глазик (милая дуга вниз)
        draw.arc(
            [eye_cx - eye_r, eye_cy - eye_r // 2, eye_cx + eye_r, eye_cy + eye_r // 2],
            start=15, end=165, fill=IRIS_NORMAL, width=3 * SCALE
        )
        # Летающие буквы Zzz
        for i in range(3):
            z_prog = ((frame_idx / FRAMES_PER_STATE) + i / 3.0) % 1.0
            zx = bx + 20 * SCALE + int(z_prog * 22 * SCALE)
            zy = by - 15 * SCALE - int(z_prog * 38 * SCALE)
            z_size = (6 + int(z_prog * 8)) * SCALE
            draw_z(draw, zx, zy, z_size, ZZZ_COLOR)

    elif state == "idle" and frame_idx == 7:
        # Моргание на последнем кадре покоя (оживляет персонажа!)
        draw.line(
            [(eye_cx - eye_r, eye_cy), (eye_cx + eye_r, eye_cy)],
            fill=OUTLINE_COLOR, width=3 * SCALE
        )
    else:
        # Открытый глаз
        draw.ellipse(
            [eye_cx - eye_r, eye_cy - eye_r, eye_cx + eye_r, eye_cy + eye_r],
            fill=SCLERA_COLOR, outline=OUTLINE_COLOR, width=2 * SCALE
        )

        # Радужка и зрачок
        look_x = -4 * SCALE if state == "walk_left" else (4 * SCALE if state == "walk_right" else 0)
        look_y = 3 * SCALE if state == "falling" else 0
        iris_r = 10 * SCALE if state in ("dragged", "falling") else 9 * SCALE
        iris_color = IRIS_SHOCK if state in ("dragged", "falling") else IRIS_NORMAL

        ix, iy = eye_cx + look_x, eye_cy + look_y
        draw.ellipse([ix - iris_r, iy - iris_r, ix + iris_r, iy + iris_r], fill=iris_color)

        # Зрачок (узкий кошачий в покое, круглый при испуге/полете)
        if state in ("dragged", "falling"):
            pr = 5 * SCALE
            draw.ellipse([ix - pr, iy - pr, ix + pr, iy + pr], fill=PUPIL_COLOR)
        else:
            pw, ph = 3 * SCALE, 7 * SCALE
            draw.ellipse([ix - pw, iy - ph, ix + pw, iy + ph], fill=PUPIL_COLOR)

        # Двойной аниме-блик в глазу
        draw.ellipse([ix - 6 * SCALE, iy - 6 * SCALE, ix - 1 * SCALE, iy - 1 * SCALE], fill="white")
        draw.ellipse([ix + 2 * SCALE, iy + 2 * SCALE, ix + 5 * SCALE, iy + 5 * SCALE], fill="white")

    # Сжимаем в 4 раза с премиум-фильтром LANCZOS для идеального сглаживания краев
    final_img = img.resize(PET_SIZE, Image.Resampling.LANCZOS)
    final_img.save(filename)


if __name__ == "__main__":
    os.makedirs("assets", exist_ok=True)
    # Удаляем старые кадры
    for old_file in glob.glob("assets/*.png"):
        os.remove(old_file)

    states = ["idle", "walk_left", "walk_right", "sleep", "falling", "dragged"]
    for st in states:
        for i in range(FRAMES_PER_STATE):
            path = f"assets/{st}_{i}.png"
            create_frame(path, st, i)
    print(f"Готово! Сгенерировано {len(states) * FRAMES_PER_STATE} детализированных HD-кадров Юки!")