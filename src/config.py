from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

PET_SIZE = (128, 128)
WINDOW_TITLE = "Yuki Desktop Pet"

ANIMATION_INTERVAL_MS = 60  # Было 100 — теперь движения станут супер-плавными!
WALK_SPEED = 3
FALL_SPEED = 14