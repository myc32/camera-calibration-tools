import cv2
import numpy as np
import json
from glob import glob
import os
from PIL import Image
import time
import sys

# === Загрузка параметров шахматной доски ===
base_dir = os.path.abspath(os.path.dirname(__file__))
config_path = os.path.join(base_dir, "../results/chessboard_config.json")

with open(config_path, "r") as f:
    config = json.load(f)

n_corners_x, n_corners_y = config["chessboard_corners"]
chessboard_size = (n_corners_x, n_corners_y)

print(f"\n📀 Размер шахматной доски: {chessboard_size} внутренних углов")
print(f"Экран: {config['screen_resolution'][0]}x{config['screen_resolution'][1]} px, диагональ {config['physical_diagonal_inch']}\"")
print(f"Размер пикселя: {config['pixel_size_cm']} см")
print(f"Размер клетки шахматной доски: {config['chessboard_cell_size_cm']} см")
print(f"Количество клеток на доске: {config['chessboard_cells']}")

# === Подготовка 3D точек ===
objp = np.zeros((n_corners_x * n_corners_y, 3), np.float32)
objp[:, :2] = np.mgrid[0:n_corners_x, 0:n_corners_y].T.reshape(-1, 2)
objp *= config["chessboard_cell_size_cm"]  # масштабируем в см

objpoints = []  # 3D точки
imgpoints = []  # 2D точки

# === Поиск изображений ===
image_extensions = ["jpg", "png", "jpeg"]
image_files = []
for ext in image_extensions:
    image_files.extend(glob(f"./data/photos/*.{ext}"))  # изменено ./photos -> ./data/photos

if not image_files:
    print("❌ Не найдено изображений в ./data/photos/")
    exit(1)

total = len(image_files)
successes = 0
failures = 0

def load_image(path):
    return cv2.imread(path)

def find_corners_with_rotations(gray, pattern_size):
    for angle in [0, 90, 180, 270]:
        if angle != 0:
            gray_rot = np.rot90(gray, k=angle // 90)
        else:
            gray_rot = gray

        ret, corners = cv2.findChessboardCornersSB(gray_rot, pattern_size)
        if ret:
            if angle != 0:
                h, w = gray.shape
                corners = corners.reshape(-1, 2)
                for i, (x, y) in enumerate(corners):
                    if angle == 90:
                        x_new, y_new = y, w - x
                    elif angle == 180:
                        x_new, y_new = w - x, h - y
                    elif angle == 270:
                        x_new, y_new = h - y, x
                    corners[i] = [x_new, y_new]
                corners = corners.reshape(-1, 1, 2)
            return True, corners
    return False, None

print(f"\n🔍 Обработка {total} изображений:")

for i, fname in enumerate(image_files, 1):
    img = load_image(fname)
    if img is None:
        print(f"\n❌ Не удалось загрузить {fname}")
        failures += 1
        continue
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    ret, corners = find_corners_with_rotations(gray, chessboard_size)

    if ret:
        objpoints.append(objp)
        criteria = (cv2.TermCriteria_EPS + cv2.TermCriteria_MAX_ITER, 30, 0.001)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)
        successes += 1
        status = "✅"
    else:
        failures += 1
        status = "⚠️"

    bar = "[" + "#" * (i * 30 // total) + " " * (30 - i * 30 // total) + "]"
    sys.stdout.write(f"\r{bar} {i}/{total} {status} {os.path.basename(fname)}")
    sys.stdout.flush()
    time.sleep(0.05)

print("\n\n📊 Результат:")
print(f"  Успешно: {successes}")
print(f"  Не найдено углов: {failures}")

if not objpoints:
    print("❌ Ни одно изображение не подходит. Выход.")
    exit(1)

# === Калибровка ===
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
)

print("\n🎯 Калибровка завершена:")

def format_length_mm(value_mm):
    if value_mm < 1:
        return f"{value_mm * 1000:.1f} мкм"
    else:
        return f"{value_mm:.3f} мм"

# Пример для iPhone 11:
sensor_width_mm = 6.3
sensor_pixel_width = 4032
sensor_pixel_size_mm = sensor_width_mm / sensor_pixel_width

cx = K[0, 2]
cy = K[1, 2]
fx = K[0, 0]
fy = K[1, 1]

cx_mm = cx * sensor_pixel_size_mm
cy_mm = cy * sensor_pixel_size_mm
f_mm_avg = ((fx + fy) / 2) * sensor_pixel_size_mm

# Внешнее ориентирование и расстояние (в сантиметрах)
R, _ = cv2.Rodrigues(rvecs[0])
camera_position = -R.T @ tvecs[0]
distance_cm = np.linalg.norm(camera_position)  # уже в см, т.к. objp в см

print(f"Матрица камеры (K):\n{K}")
print(f"Коэффициенты дисторсии:\n{dist.ravel()}")

print("\nГлавная точка (principal point):")
print(f"  В пикселях: cx = {cx:.2f}, cy = {cy:.2f}")
print(f"  В физическом размере: cx = {format_length_mm(cx_mm)}, cy = {format_length_mm(cy_mm)}")

print("\nФокусное расстояние (focal length):")
print(f"  В пикселях: f = {(fx + fy) / 2:.2f}")
print(f"  В физическом размере: f = {format_length_mm(f_mm_avg)}")

print(f"\nРасстояние до шахматной доски: {distance_cm:.2f} см")

# === Сохранение результатов в текстовый файл ===
with open("results/calibration_results.txt", "w") as f:  # изменено ./calibration_results.txt -> ./results/calibration_results.txt
    f.write("Калибровка камеры\n")
    f.write("=================\n\n")

    f.write(f"Матрица камеры (K):\n{K}\n\n")
    f.write(f"Коэффициенты дисторсии:\n{dist.ravel()}\n\n")

    f.write("Главная точка (principal point):\n")
    f.write(f"  В пикселях: cx = {cx:.2f}, cy = {cy:.2f}\n")
    f.write(f"  В физическом размере: cx = {format_length_mm(cx_mm)}, cy = {format_length_mm(cy_mm)}\n\n")

    f.write("Фокусное расстояние (focal length):\n")
    f.write(f"  В пикселях: f = {(fx + fy) / 2:.2f}\n")
    f.write(f"  В физическом размере: f = {format_length_mm(f_mm_avg)}\n\n")

    f.write(f"Расстояние до шахматной доски: {distance_cm:.2f} см\n")

# === Внешнее ориентирование (первое изображение) ===
external_data = {
    "camera_position_cm": {
        "X": round(camera_position[0][0], 2),
        "Y": round(camera_position[1][0], 2),
        "Z": round(camera_position[2][0], 2),
        "distance_to_chessboard_center_cm": round(distance_cm, 2)
    },
    "rotation_matrix": R.tolist(),
    "translation_vector": tvecs[0].ravel().tolist()
}

print("\n📍 Внешнее ориентирование камеры (по первому кадру):")
print(f"  X: {external_data['camera_position_cm']['X']} см")
print(f"  Y: {external_data['camera_position_cm']['Y']} см")
print(f"  Z: {external_data['camera_position_cm']['Z']} см")
print(f"  📏 Расстояние до шахматной доски: {external_data['camera_position_cm']['distance_to_chessboard_center_cm']} см")

with open("results/external_orientation.json", "w") as f:  # изменено ./external_orientation.json -> ./results/external_orientation.json
    json.dump(external_data, f, indent=2)

print("\n📂 Результаты сохранены в results/calibration_results.txt и results/external_orientation.json")
