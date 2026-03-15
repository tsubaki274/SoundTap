from __future__ import annotations

from collections.abc import Callable


def is_valid_hotkey_expression(expression: str) -> bool:
    if not expression.strip():
        return False

    try:
        from pynput import keyboard

        keyboard.HotKey.parse(expression)
    except (ImportError, ValueError):
        return False

    return True


DEFAULT_HOTKEY_TOGGLE_ENABLED = "<ctrl>+<alt>+s"
DEFAULT_HOTKEY_TOGGLE_MUTE = "<ctrl>+<alt>+m"
DEFAULT_HOTKEY_RELOAD_CONFIG = "<ctrl>+<alt>+r"


class GlobalHotkeyManager:
    def __init__(self, hotkeys: dict[str, Callable[[], None]]) -> None:
        self._hotkeys = hotkeys
        self._listener: object | None = None

    def start(self) -> None:
        if self._listener is not None:
            return

        from pynput import keyboard

        listener = keyboard.GlobalHotKeys(self._hotkeys)
        listener.start()
        self._listener = listener

    def stop(self) -> None:
        listener = self._listener
        if listener is None:
            return

        stop = getattr(listener, "stop", None)
        if callable(stop):
            stop()
        self._listener = None
