from pathlib import Path

# Базовый путь к проекту
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

# Настройки питомца
PET_SIZE = (128, 128)
WINDOW_TITLE = "Desktop Pet"