import pygame
import math
import json
import os
import subprocess

# === Входные данные ===
# При запуске спрашиваем диагональ экрана у пользователя
def input_float(prompt, default):
    try:
        value = input(f"{prompt} (по умолчанию {default}): ").strip()
        return float(value) if value else default
    except ValueError:
        print("Некорректное значение, используется значение по умолчанию.")
        return default

TV_DIAGONAL_INCHES = input_float("Введите диагональ экрана (в дюймах)", 13.6)  # MacBook Air M3 13.6" по умолчанию
FILL_RATIO = 0.9                # Процент экрана, занимаемый шахматкой
MIN_CELL_CM = 1.5               # Минимальный размер клетки в см
MAX_CELL_CM = 2.5               # Максимальный размер клетки в см
MAX_CORNERS_X = 15              # Максимум пересечений (углов) по ширине
MAX_CORNERS_Y = 11              # Максимум пересечений по высоте

# === Получаем список мониторов через pygame ===
pygame.init()
monitors = pygame.display.get_desktop_sizes()

print("Доступные мониторы:")
for i, (w, h) in enumerate(monitors):
    print(f"Monitor {i}: resolution: {w}x{h}")

# === Определяем целевой монитор ===
if len(monitors) > 1:
    target_index = 1
    print("Используем внешний монитор (номер 1)")
else:
    target_index = 0
    print("Внешний монитор не найден, используем первый доступный монитор")

width_px, height_px = monitors[target_index]

# --- Попытка получить физическое разрешение macOS через system_profiler ---
def get_macos_physical_resolution():
    try:
        output = subprocess.check_output(
            "system_profiler SPDisplaysDataType | grep Resolution | head -1",
            shell=True,
            text=True
        ).strip()
        # output пример: "Resolution: 2560 x 1600 Retina"
        parts = output.split()
        # ищем первые два числа подряд (ширина и высота)
        for i in range(len(parts)):
            if parts[i].isdigit() and i + 2 < len(parts) and parts[i+2].isdigit():
                width = int(parts[i])
                height = int(parts[i+2])
                return width, height
        raise ValueError("Не удалось распарсить разрешение из строки: " + output)
    except Exception as e:
        print("Ошибка получения физического разрешения macOS:", e)
        return None, None

# Если Mac, пытаемся получить физическое разрешение и скорректировать
physical_res = get_macos_physical_resolution()
if physical_res is not None:
    phys_w, phys_h = physical_res
    print(f"Физическое разрешение macOS: {phys_w}x{phys_h}")
    # Если отличается от вывода pygame — заменяем
    if phys_w > width_px and phys_h > height_px:
        print("Корректируем разрешение с масштабом Retina")
        width_px, height_px = phys_w, phys_h

# === Вычисляем размеры экрана и параметры шахматной доски ===
diagonal_px = math.sqrt(width_px**2 + height_px**2)
pixel_size_cm = (TV_DIAGONAL_INCHES * 2.54) / diagonal_px

screen_width_cm = width_px * pixel_size_cm
screen_height_cm = height_px * pixel_size_cm

# === Определяем количество клеток ===
usable_width_cm = screen_width_cm * FILL_RATIO
usable_height_cm = screen_height_cm * FILL_RATIO

cell_size_cm = (MIN_CELL_CM + MAX_CELL_CM) / 2
n_cells_x = int(usable_width_cm / cell_size_cm)
n_cells_y = int(usable_height_cm / cell_size_cm)

# Гарантируем чётное количество клеток
n_cells_x = n_cells_x if n_cells_x % 2 == 0 else n_cells_x - 1
n_cells_y = n_cells_y if n_cells_y % 2 == 0 else n_cells_y - 1

# Переводим в углы (внутренние пересечения)
n_corners_x = min(n_cells_x - 1, MAX_CORNERS_X)
n_corners_y = min(n_cells_y - 1, MAX_CORNERS_Y)

n_cells_x = n_corners_x + 1
n_cells_y = n_corners_y + 1

cell_width = width_px // n_cells_x
cell_height = height_px // n_cells_y

# === Инициализация Pygame ===
screen = pygame.display.set_mode((width_px, height_px), pygame.FULLSCREEN, display=target_index)
pygame.display.set_caption("Chessboard")

# Скрываем курсор
pygame.mouse.set_visible(False)

# === Рисуем шахматную доску ===
for y in range(n_cells_y):
    for x in range(n_cells_x):
        color = (255, 255, 255) if (x + y) % 2 == 0 else (0, 0, 0)
        rect = pygame.Rect(x * cell_width, y * cell_height, cell_width, cell_height)
        pygame.draw.rect(screen, color, rect)

pygame.display.flip()

# === Подготовка конфигурации для сохранения ===
config = {
    "screen_resolution": [width_px, height_px],
    "physical_diagonal_inch": TV_DIAGONAL_INCHES,
    "pixel_size_cm": round(pixel_size_cm, 5),
    "chessboard_cell_size_cm": round((cell_width + cell_height) * 0.5 * pixel_size_cm, 2),
    "chessboard_corners": [n_corners_x, n_corners_y],
    "chessboard_cells": [n_cells_x, n_cells_y],
    "chessboard_display_ratio": FILL_RATIO,
    "target_display_index": target_index
}

# === Создаем папку results если нет ===
save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../results"))
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

save_path = os.path.join(save_dir, "chessboard_config.json")

with open(save_path, "w") as f:
    json.dump(config, f, indent=2)

print(f"\nChessboard parameters saved to {save_path}:")
print(json.dumps(config, indent=2))

# === Ждём нажатия ESC для выхода ===
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type == pygame.QUIT:
            running = False

pygame.quit()
