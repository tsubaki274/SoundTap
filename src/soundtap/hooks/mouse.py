from __future__ import annotations

from collections.abc import Callable
from time import monotonic
from typing import Any


class MouseHook:
    def __init__(
        self,
        on_click: Callable[[str], None],
        on_scroll: Callable[[str], None],
        scroll_cooldown_seconds: float = 0.15,
    ) -> None:
        self._on_click = on_click
        self._on_scroll = on_scroll
        self._scroll_cooldown_seconds = max(0.0, scroll_cooldown_seconds)
        self._last_scroll_at: dict[str, float] = {}
        self._listener: Any | None = None

    def start(self) -> None:
        if self._listener is not None:
            return

        from pynput import mouse as pynput_mouse

        listener = pynput_mouse.Listener(
            on_click=self._handle_native_click,
            on_scroll=self._handle_native_scroll,
        )
        listener.start()
        self._listener = listener

    def stop(self) -> None:
        listener = self._listener
        if listener is None:
            return

        listener.stop()
        self._listener = None

    def handle_click(self, button: object, pressed: bool) -> None:
        if not pressed:
            return

        button_name = normalize_mouse_button_name(button)
        if button_name is None:
            return

        self._on_click(button_name)

    def _handle_native_click(
        self, _x: int, _y: int, button: object, pressed: bool
    ) -> None:
        self.handle_click(button, pressed)

    def handle_scroll(self, dy: int) -> None:
        direction = normalize_mouse_scroll_direction(dy)
        if direction is None:
            return

        now = monotonic()
        last_scroll_at = self._last_scroll_at.get(
            direction, -self._scroll_cooldown_seconds
        )
        if now - last_scroll_at < self._scroll_cooldown_seconds:
            return

        self._last_scroll_at[direction] = now

        self._on_scroll(direction)

    def _handle_native_scroll(self, _x: int, _y: int, _dx: int, dy: int) -> None:
        self.handle_scroll(dy)


def normalize_mouse_button_name(button: object) -> str | None:
    if isinstance(button, str):
        return _normalize_button_text(button)

    name = getattr(button, "name", None)
    if isinstance(name, str) and name:
        return _normalize_button_text(name)

    return _normalize_button_text(str(button))


def _normalize_button_text(text: str) -> str | None:
    candidate = text.strip()
    if not candidate:
        return None

    if candidate.startswith("Button."):
        candidate = candidate[7:]

    return candidate.lower()


def normalize_mouse_scroll_direction(dy: int) -> str | None:
    if dy > 0:
        return "wheel_up"
    if dy < 0:
        return "wheel_down"
    return None
