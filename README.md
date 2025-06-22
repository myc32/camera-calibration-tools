# Calibration iPhone 11

Проект для калибровки камеры iPhone 11 с использованием OpenCV и изображений шахматной доски.

## Структура проекта

Calibration_iPhone11/
├── README.md                   # Этот файл
├── chessboard_config.json      # Конфигурация шахматной доски и параметров экрана
├── code/                      # Исходный код калибровки
│   ├── camera_calibration.py
│   └── fullscreen_chessboard.py
├── data/                      # Исходные данные (фотографии шахматной доски)
│   └── photos/
├── requirements.txt           # Зависимости Python проекта
├── results/                   # Результаты калибровки
│   ├── calibration_results.txt
│   └── external_orientation.json
└── venv/                      # Виртуальное окружение Python

## Установка и запуск

1. Клонируйте репозиторий и перейдите в папку проекта:

```bash
git clone https://github.com/myc32/camera-calibration-tools.git
cd camera-calibration-tools/Calibration_iPhone11

Создайте и активируйте виртуальное окружение:

python3 -m venv venv
source venv/bin/activate      # для Linux/macOS
.\venv\Scripts\activate       # для Windows
Установите зависимости:

pip install -r requirements.txt
Поместите фотографии шахматной доски в папку data/photos/.

Запустите калибровку:
python code/camera_calibration.py
Результаты
Файлы с результатами сохраняются в папку results/.

calibration_results.txt — текстовый отчет по калибровке.

external_orientation.json — данные внешнего ориентирования камеры.

Конфигурация
Параметры шахматной доски и экрана задаются в chessboard_config.json.
