from PyQt6.QtWidgets import QWidget, QLabel, QApplication
from PyQt6.QtCore import Qt, QPoint, QTimer, QRect
from PyQt6.QtGui import QMouseEvent, QPixmap

from src.config import PET_SIZE, ANIMATION_INTERVAL_MS, ASSETS_DIR
from src.pet_logic import PetLogic, PetState


class AssetManager:
    def __init__(self):
        self._cache: dict[PetState, list[QPixmap]] = {}
        self._load_all_assets()

    def _load_all_assets(self):
        for state in PetState:
            frames = []
            frame_files = sorted(ASSETS_DIR.glob(f"{state.value}_*.png"))
            for file_path in frame_files:
                pixmap = QPixmap(str(file_path)).scaled(
                    *PET_SIZE, Qt.AspectRatioMode.KeepAspectRatio
                )
                frames.append(pixmap)
            self._cache[state] = frames

    def get_frame(self, state: PetState, frame_index: int) -> QPixmap | None:
        # Если для FALLING или DRAGGED еще нет своих картинок — используем IDLE как запасной вариант
        frames = self._cache.get(state) or self._cache.get(PetState.IDLE, [])
        if not frames:
            return None
        return frames[frame_index % len(frames)]


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_position = QPoint()
        self._is_dragging = False

        self.logic = PetLogic()
        self.assets = AssetManager()

        self._init_ui()
        self._spawn_on_floor()
        self._init_timer()

    def _init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(*PET_SIZE)

        self.label = QLabel(self)
        self.label.resize(*PET_SIZE)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def _get_screen_bounds(self) -> tuple[int, int, int]:
        """Возвращает (min_x, max_x, floor_y) с учетом панели задач."""
        screen: QRect = QApplication.primaryScreen().availableGeometry()
        min_x = screen.left()
        max_x = screen.right() - self.width()
        floor_y = screen.bottom() - self.height()
        return min_x, max_x, floor_y

    def _spawn_on_floor(self):
        """Ставит Юки по центру экрана прямо на панель задач при старте."""
        min_x, max_x, floor_y = self._get_screen_bounds()
        start_x = (min_x + max_x) // 2
        self.move(start_x, floor_y)

    def _init_timer(self):
        self.timer = QTimer(self)
        self.timer.setInterval(ANIMATION_INTERVAL_MS)
        self.timer.timeout.connect(self._game_loop)
        self.timer.start()

    def _game_loop(self):
        if not self._is_dragging:
            min_x, max_x, floor_y = self._get_screen_bounds()
            new_x, new_y = self.logic.update(self.x(), self.y(), min_x, max_x, floor_y)
            self.move(new_x, new_y)

        self._render_frame()

    def _render_frame(self):
        pixmap = self.assets.get_frame(self.logic.state, self.logic.frame_index)
        if pixmap:
            self.label.setPixmap(pixmap)
        else:
            self.label.setText(f"🐱\n{self.logic.state.value}")

    # --- Интерактив с мышкой ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self.logic.set_state(PetState.DRAGGED)
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self._is_dragging:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            # Если отпустили ниже панели задач — сразу возвращаем на пол
            _, _, floor_y = self._get_screen_bounds()
            if self.y() > floor_y:
                self.move(self.x(), floor_y)
                self.logic.set_state(PetState.IDLE)
            event.accept()