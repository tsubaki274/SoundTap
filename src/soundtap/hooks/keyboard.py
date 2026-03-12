from __future__ import annotations

from collections.abc import Callable
from typing import Any


SPECIAL_KEY_ALIASES = {
    " ": "space",
    "esc": "escape",
    "return": "enter",
    "ctrl_l": "ctrl",
    "ctrl_r": "ctrl",
    "alt_l": "alt",
    "alt_r": "alt",
    "shift_l": "shift",
    "shift_r": "shift",
}


class KeyboardHook:
    def __init__(self, on_press: Callable[[str], None]) -> None:
        self._on_press = on_press
        self._pressed_keys: set[str] = set()
        self._listener: Any | None = None

    def start(self) -> None:
        if self._listener is not None:
            return

        from pynput import keyboard as pynput_keyboard

        listener = pynput_keyboard.Listener(
            on_press=self.handle_key_press,
            on_release=self.handle_key_release,
        )
        listener.start()
        self._listener = listener

    def stop(self) -> None:
        listener = self._listener
        if listener is None:
            return

        listener.stop()
        self._listener = None
        self._pressed_keys.clear()

    def handle_key_press(self, key: object) -> None:
        key_name = normalize_key_name(key)
        if key_name is None or key_name in self._pressed_keys:
            return

        self._pressed_keys.add(key_name)
        self._on_press(key_name)

    def handle_key_release(self, key: object) -> None:
        key_name = normalize_key_name(key)
        if key_name is None:
            return

        self._pressed_keys.discard(key_name)


def normalize_key_name(key: object) -> str | None:
    if isinstance(key, str):
        return _normalize_key_text(key)

    char = getattr(key, "char", None)
    if isinstance(char, str) and char:
        return _normalize_key_text(char)

    name = getattr(key, "name", None)
    if isinstance(name, str) and name:
        return _normalize_key_text(name)

    return _normalize_key_text(str(key))


def _normalize_key_text(text: str) -> str | None:
    candidate = text.strip()
    if text == " ":
        candidate = " "

    if not candidate:
        return None

    if candidate.startswith("Key."):
        candidate = candidate[4:]

    normalized = SPECIAL_KEY_ALIASES.get(candidate.lower(), candidate.lower())
    return normalized or None
