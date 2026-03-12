from __future__ import annotations

import logging
import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from platformdirs import user_config_dir

from soundtap.hooks.hotkeys import (
    DEFAULT_HOTKEY_RELOAD_CONFIG,
    DEFAULT_HOTKEY_TOGGLE_ENABLED,
    DEFAULT_HOTKEY_TOGGLE_MUTE,
)
from soundtap.hooks.keyboard import normalize_key_name
from soundtap.hooks.mouse import normalize_mouse_button_name


logger = logging.getLogger(__name__)

DEFAULT_CONFIG_TEMPLATE = """# SoundTap の設定ファイル
# path には再生したい mp3 ファイルのパスを指定します。
# volume は 0 から 100 の範囲で指定します。
# Windows パスは `C:/Sounds/a.mp3` のように `/` を使うと安全です。
# `C:\\Sounds\\a.mp3` のように `\\` を重ねて書いても構いません。

[app]
master_volume = 80
scroll_cooldown_ms = 150

[hotkeys]
toggle_enabled = "<ctrl>+<alt>+s"
toggle_mute = "<ctrl>+<alt>+m"
reload_config = "<ctrl>+<alt>+r"

[keyboard.default]
path = "C:/Sounds/type.mp3"
volume = 50

[keyboard.a]
path = "C:/Sounds/a.mp3"
volume = 100

[keyboard.enter]
path = "C:/Sounds/enter.mp3"
volume = 70

[mouse.default]
path = "C:/Sounds/mouse.mp3"
volume = 50

[mouse.left]
path = "C:/Sounds/click.mp3"
volume = 50

[mouse.right]
path = "C:/Sounds/right.mp3"
volume = 60

[mouse.wheel_up]
path = "C:/Sounds/wheel-up.mp3"
volume = 40

[mouse.wheel_down]
path = "C:/Sounds/wheel-down.mp3"
volume = 40
"""


@dataclass(frozen=True, slots=True)
class SoundBinding:
    path: Path
    volume: float = 1.0

    def effective_volume(self, master_volume: float) -> float:
        normalized_master = max(0.0, min(100.0, master_volume)) / 100.0
        normalized_volume = max(0.0, min(100.0, self.volume)) / 100.0
        return max(0.0, min(1.0, normalized_master * normalized_volume))


@dataclass(frozen=True, slots=True)
class AppSettings:
    master_volume: float = 100.0
    scroll_cooldown_ms: int = 150
    hotkeys: dict[str, str] = field(default_factory=dict)
    keyboard_default: SoundBinding | None = None
    mouse_default: SoundBinding | None = None
    keyboard: dict[str, SoundBinding] = field(default_factory=dict)
    mouse: dict[str, SoundBinding] = field(default_factory=dict)


class SettingsStore:
    def __init__(self, config_dir: Path | None = None) -> None:
        default_dir = Path(user_config_dir("SoundTap", "SoundTap"))
        self.config_dir = config_dir or default_dir
        self.config_path = self.config_dir / "config.toml"

    def ensure_exists(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.config_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")

    def load(self) -> AppSettings:
        self.ensure_exists()

        content = self.config_path.read_text(encoding="utf-8")

        try:
            data = tomllib.loads(content)
        except tomllib.TOMLDecodeError as exc:
            recovered_data = _load_with_windows_path_fallback(content)
            if recovered_data is None:
                logger.warning("Invalid TOML in %s: %s", self.config_path, exc)
                return AppSettings()

            logger.warning(
                "Recovered invalid TOML in %s by normalizing Windows path separators",
                self.config_path,
            )
            data = recovered_data

        return parse_settings(data, base_dir=self.config_dir)


def _load_with_windows_path_fallback(content: str) -> dict[str, Any] | None:
    pattern = re.compile(r'^(\s*path\s*=\s*)"([^"\n]*)"(\s*)$', re.MULTILINE)

    def replace_path(match: re.Match[str]) -> str:
        prefix, raw_path, suffix = match.groups()
        normalized_path = raw_path.replace("\\", "/")
        return f'{prefix}"{normalized_path}"{suffix}'

    sanitized = pattern.sub(replace_path, content)
    if sanitized == content:
        return None

    try:
        data = tomllib.loads(sanitized)
    except tomllib.TOMLDecodeError:
        return None

    return data


def parse_settings(data: dict[str, Any], base_dir: Path) -> AppSettings:
    app_section = data.get("app")
    master_volume = _parse_master_volume(app_section)

    keyboard_section = data.get("keyboard")
    mouse_section = data.get("mouse")

    return AppSettings(
        master_volume=master_volume,
        scroll_cooldown_ms=_parse_scroll_cooldown_ms(app_section),
        hotkeys=_parse_hotkeys(data.get("hotkeys")),
        keyboard_default=_parse_default_keyboard_binding(keyboard_section, base_dir),
        mouse_default=_parse_default_mouse_binding(mouse_section, base_dir),
        keyboard=_parse_bindings(
            keyboard_section, base_dir, normalize_key_name, "keyboard"
        ),
        mouse=_parse_bindings(
            mouse_section, base_dir, normalize_mouse_button_name, "mouse"
        ),
    )


def _parse_master_volume(app_section: object) -> float:
    if not isinstance(app_section, dict):
        return 100.0

    volume = app_section.get("master_volume", 100.0)
    return _coerce_volume(volume, context="app.master_volume") or 100.0


def _parse_scroll_cooldown_ms(app_section: object) -> int:
    if not isinstance(app_section, dict):
        return 150

    raw_value = app_section.get("scroll_cooldown_ms", 150)
    if isinstance(raw_value, bool):
        logger.warning("Ignored boolean scroll cooldown value")
        return 150

    try:
        cooldown = int(raw_value)
    except (TypeError, ValueError):
        logger.warning("Ignored invalid scroll cooldown value")
        return 150

    if cooldown < 0 or cooldown > 5000:
        logger.warning("Ignored out-of-range scroll cooldown value")
        return 150

    return cooldown


def _parse_hotkeys(hotkeys_section: object) -> dict[str, str]:
    defaults = {
        "toggle_enabled": DEFAULT_HOTKEY_TOGGLE_ENABLED,
        "toggle_mute": DEFAULT_HOTKEY_TOGGLE_MUTE,
        "reload_config": DEFAULT_HOTKEY_RELOAD_CONFIG,
    }
    if not isinstance(hotkeys_section, dict):
        return defaults

    parsed_hotkeys = defaults.copy()
    for key, default_value in defaults.items():
        configured_value = hotkeys_section.get(key, default_value)
        if isinstance(configured_value, str) and configured_value.strip():
            parsed_hotkeys[key] = configured_value.strip()

    return parsed_hotkeys


def _parse_default_keyboard_binding(
    keyboard_section: object, base_dir: Path
) -> SoundBinding | None:
    if not isinstance(keyboard_section, dict):
        return None

    raw_default = keyboard_section.get("default")
    if raw_default is None:
        return None

    binding = _parse_single_binding(
        raw_name="default",
        raw_config=raw_default,
        base_dir=base_dir,
        section_name="keyboard",
    )
    if binding is None:
        logger.warning("Ignored invalid keyboard.default binding")

    return binding


def _parse_default_mouse_binding(
    mouse_section: object, base_dir: Path
) -> SoundBinding | None:
    if not isinstance(mouse_section, dict):
        return None

    raw_default = mouse_section.get("default")
    if raw_default is None:
        return None

    binding = _parse_single_binding(
        raw_name="default",
        raw_config=raw_default,
        base_dir=base_dir,
        section_name="mouse",
    )
    if binding is None:
        logger.warning("Ignored invalid mouse.default binding")

    return binding


def _parse_bindings(
    section: object,
    base_dir: Path,
    normalize_name: Callable[[object], str | None],
    section_name: str,
) -> dict[str, SoundBinding]:
    if not isinstance(section, dict):
        return {}

    bindings: dict[str, SoundBinding] = {}
    for raw_name, raw_config in section.items():
        if raw_name == "default":
            continue

        normalized_name = normalize_name(raw_name)
        if normalized_name is None:
            logger.warning(
                "Ignored invalid %s binding name: %s", section_name, raw_name
            )
            continue

        binding = _parse_single_binding(
            raw_name=normalized_name,
            raw_config=raw_config,
            base_dir=base_dir,
            section_name=section_name,
        )
        if binding is None:
            continue

        bindings[normalized_name] = binding

    return bindings


def _parse_single_binding(
    raw_name: str,
    raw_config: object,
    base_dir: Path,
    section_name: str,
) -> SoundBinding | None:
    if not isinstance(raw_config, dict):
        logger.warning("Ignored invalid %s binding body for %s", section_name, raw_name)
        return None

    raw_path = raw_config.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        logger.warning("Ignored %s binding without path: %s", section_name, raw_name)
        return None

    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (base_dir / path).resolve()

    if _is_disallowed_sound_path(path):
        logger.warning(
            "Ignored %s binding with disallowed path: %s", section_name, raw_path
        )
        return None

    volume = _coerce_volume(
        raw_config.get("volume", 1.0),
        context=f"{section_name}.{raw_name}.volume",
    )
    if volume is None:
        return None

    return SoundBinding(path=path, volume=volume)


def _coerce_volume(value: object, context: str) -> float | None:
    if isinstance(value, bool):
        logger.warning("Ignored boolean volume value for %s", context)
        return None

    if not isinstance(value, (int, float, str)):
        logger.warning("Ignored unsupported volume value for %s", context)
        return None

    convertible_value: int | float | str = value

    try:
        volume = float(convertible_value)
    except (TypeError, ValueError):
        logger.warning("Ignored non-numeric volume value for %s", context)
        return None

    if not 0.0 <= volume <= 100.0:
        logger.warning("Ignored out-of-range volume value for %s", context)
        return None

    return volume


def _is_disallowed_sound_path(path: Path) -> bool:
    path_text = str(path)
    return path_text.startswith("\\\\")
