import random
from dataclasses import dataclass
from enum import Enum
from src.config import WALK_SPEED, FALL_SPEED


class PetState(Enum):
    IDLE = "idle"
    WALK_LEFT = "walk_left"
    WALK_RIGHT = "walk_right"
    SLEEP = "sleep"        # Новое состояние сна!
    FALLING = "falling"
    DRAGGED = "dragged"


@dataclass(frozen=True)
class StateBehavior:
    dx: int
    dy: int
    min_ticks: int
    max_ticks: int
    transitions: dict[PetState, float]


STATE_REGISTRY: dict[PetState, StateBehavior] = {
    PetState.IDLE: StateBehavior(
        dx=0, dy=0, min_ticks=30, max_ticks=70,
        transitions={
            PetState.IDLE: 0.20,
            PetState.WALK_LEFT: 0.35,
            PetState.WALK_RIGHT: 0.35,
            PetState.SLEEP: 0.10,      # 10% шанс сладко уснуть после стояния!
        }
    ),
    PetState.WALK_LEFT: StateBehavior(
        dx=-WALK_SPEED, dy=0, min_ticks=30, max_ticks=70,
        transitions={
            PetState.IDLE: 0.7,
            PetState.WALK_RIGHT: 0.3,
        }
    ),
    PetState.WALK_RIGHT: StateBehavior(
        dx=WALK_SPEED, dy=0, min_ticks=30, max_ticks=70,
        transitions={
            PetState.IDLE: 0.7,
            PetState.WALK_LEFT: 0.3,
        }
    ),
    # Сон: от 1200 до 1800 тиков (2–3 минуты реального времени)
    PetState.SLEEP: StateBehavior(
        dx=0, dy=0, min_ticks=1200, max_ticks=1800,
        transitions={
            PetState.IDLE: 1.0,        # Проснувшись, сначала просто сидит
        }
    ),
    PetState.FALLING: StateBehavior(
        dx=0, dy=FALL_SPEED, min_ticks=9999, max_ticks=9999,
        transitions={PetState.IDLE: 1.0}
    ),
    PetState.DRAGGED: StateBehavior(
        dx=0, dy=0, min_ticks=9999, max_ticks=9999,
        transitions={PetState.FALLING: 1.0}
    ),
}


class PetLogic:
    def __init__(self):
        self.state = PetState.IDLE
        self.frame_index = 0
        self._ticks_in_state = 0
        self._max_ticks = self._get_random_duration()

    @property
    def current_behavior(self) -> StateBehavior:
        return STATE_REGISTRY[self.state]

    def _get_random_duration(self) -> int:
        b = self.current_behavior
        return random.randint(b.min_ticks, b.max_ticks)

    def set_state(self, new_state: PetState):
        if self.state != new_state:
            self.state = new_state
            self._ticks_in_state = 0
            self.frame_index = 0
            self._max_ticks = self._get_random_duration()

    def update(self, x: int, y: int, min_x: int, max_x: int, floor_y: int) -> tuple[int, int]:
        self._ticks_in_state += 1
        self.frame_index += 1

        # 1. Гравитация (даже если спящего кота поднять — он проснется и упадет)
        if y < floor_y:
            self.set_state(PetState.FALLING)
            new_y = min(y + self.current_behavior.dy, floor_y)
            return x, new_y

        if self.state == PetState.FALLING and y >= floor_y:
            self.set_state(PetState.IDLE)
            y = floor_y

        # 2. Переход по таймеру
        if self._ticks_in_state >= self._max_ticks:
            self._transition_to_next_state()

        # 3. Движение и стены
        new_x = x + self.current_behavior.dx

        if new_x <= min_x:
            new_x = min_x
            self.set_state(PetState.WALK_RIGHT)
        elif new_x >= max_x:
            new_x = max_x
            self.set_state(PetState.WALK_LEFT)

        return new_x, floor_y

    def _transition_to_next_state(self):
        transitions = self.current_behavior.transitions
        states = list(transitions.keys())
        weights = list(transitions.values())
        self.set_state(random.choices(states, weights=weights, k=1)[0])