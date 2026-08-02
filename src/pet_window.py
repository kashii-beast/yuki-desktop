from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QMouseEvent, QColor
from src.config import PET_SIZE

class PetWindow(QWidget):
    """Окно питомца: без рамок, поверх всех окон, с поддержкой перетаскивания."""

    def __init__(self):
        super().__init__()
        self._drag_position = QPoint()
        self._init_ui()

    def _init_ui(self):
        # 1. Убираем рамки и делаем окно всегда поверх остальных
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.SubWindow
        )
        
        # 2. Включаем прозрачный фон окна
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.resize(*PET_SIZE)

        # Placeholder — заглушка, пока нет нормального спрайта
        self.label = QLabel("🐱", self)
        self.label.setStyleSheet("font-size: 80px;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.resize(*PET_SIZE)

    # --- Логика перетаскивания питомца мышкой ---
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Запоминаем смещение курсора относительно угла окна
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Перемещаем окно вслед за курсором
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()