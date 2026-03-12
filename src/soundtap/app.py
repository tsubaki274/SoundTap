from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from soundtap.audio.player import AudioPlayer
from soundtap.config.settings import AppSettings, SettingsStore
from soundtap.hooks.hotkeys import GlobalHotkeyManager
from soundtap.hooks.keyboard import KeyboardHook
from soundtap.hooks.mouse import MouseHook
from soundtap.tray.icon import TrayIconApp


logger = logging.getLogger(__name__)


class SoundTapApp:
    def __init__(self, settings_store: SettingsStore | None = None) -> None:
        self._settings_store = settings_store or SettingsStore()
        self._settings: AppSettings = AppSettings()
        self._audio_player = AudioPlayer()
        self._keyboard_hook = KeyboardHook(self._handle_keyboard_press)
        self._mouse_hook = self._create_mouse_hook()
        self._hotkey_manager: GlobalHotkeyManager | None = None
        self._running = False
        self._muted = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_muted(self) -> bool:
        return self._muted

    @property
    def config_dir(self) -> Path:
        return self._settings_store.config_dir

    @property
    def config_path(self) -> Path:
        return self._settings_store.config_path

    def run(self) -> None:
        self.reload_settings()
        self._start_hotkeys()
        tray_app = TrayIconApp(self)
        tray_app.run()

    def start(self) -> bool:
        if self._running:
            return True

        self.reload_settings()

        try:
            self._audio_player.initialize()
            self._keyboard_hook.start()
            self._mouse_hook.start()
        except Exception:
            logger.exception("Failed to start SoundTap listeners")
            self._keyboard_hook.stop()
            self._mouse_hook.stop()
            self._audio_player.shutdown()
            return False

        self._running = True
        logger.info("SoundTap started")
        return True

    def stop(self) -> None:
        if not self._running:
            return

        self._keyboard_hook.stop()
        self._mouse_hook.stop()
        self._audio_player.stop_all()
        self._running = False
        logger.info("SoundTap stopped")

    def shutdown(self) -> None:
        self.stop()
        self._stop_hotkeys()
        self._audio_player.shutdown()

    def reload_settings(self) -> AppSettings:
        was_running = self._running
        if was_running:
            self._keyboard_hook.stop()
            self._mouse_hook.stop()

        self._settings = self._settings_store.load()
        self._mouse_hook = self._create_mouse_hook()
        self._audio_player.clear_cache()

        if was_running:
            try:
                self._keyboard_hook.start()
                self._mouse_hook.start()
            except Exception:
                self._running = False
                logger.exception("Failed to restart SoundTap listeners after reload")
            self._restart_hotkeys()

        logger.info("Settings loaded from %s", self.config_path)
        return self._settings

    def toggle_enabled(self) -> bool:
        if self._running:
            self.stop()
            return False

        return self.start()

    def toggle_mute(self) -> bool:
        self._muted = not self._muted
        logger.info("SoundTap muted=%s", self._muted)
        return self._muted

    def open_config_dir(self) -> None:
        path = self.config_dir
        if sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
            return

        command = (
            ["open", str(path)] if sys.platform == "darwin" else ["xdg-open", str(path)]
        )
        subprocess.run(command, check=False)

    def _handle_keyboard_press(self, key_name: str) -> None:
        if self._muted:
            return

        binding = self._settings.keyboard.get(key_name)
        if binding is None:
            binding = self._settings.keyboard_default

        if binding is None:
            return

        self._audio_player.play(
            binding.path, binding.effective_volume(self._settings.master_volume)
        )

    def _handle_mouse_click(self, button_name: str) -> None:
        if self._muted:
            return

        binding = self._settings.mouse.get(button_name)
        if binding is None:
            binding = self._settings.mouse_default

        if binding is None:
            return

        self._audio_player.play(
            binding.path, binding.effective_volume(self._settings.master_volume)
        )

    def _handle_mouse_scroll(self, direction_name: str) -> None:
        if self._muted:
            return

        binding = self._settings.mouse.get(direction_name)
        if binding is None:
            binding = self._settings.mouse_default

        if binding is None:
            return

        self._audio_player.play(
            binding.path, binding.effective_volume(self._settings.master_volume)
        )

    def _start_hotkeys(self) -> None:
        if self._hotkey_manager is not None:
            return

        def on_toggle_enabled() -> None:
            self.toggle_enabled()

        def on_toggle_mute() -> None:
            self.toggle_mute()

        def on_reload_config() -> None:
            self.reload_settings()

        self._hotkey_manager = GlobalHotkeyManager(
            {
                self._settings.hotkeys["toggle_enabled"]: on_toggle_enabled,
                self._settings.hotkeys["toggle_mute"]: on_toggle_mute,
                self._settings.hotkeys["reload_config"]: on_reload_config,
            }
        )
        self._hotkey_manager.start()

    def _stop_hotkeys(self) -> None:
        if self._hotkey_manager is None:
            return

        self._hotkey_manager.stop()
        self._hotkey_manager = None

    def _restart_hotkeys(self) -> None:
        self._stop_hotkeys()
        self._start_hotkeys()

    def _create_mouse_hook(self) -> MouseHook:
        return MouseHook(
            self._handle_mouse_click,
            self._handle_mouse_scroll,
            scroll_cooldown_seconds=self._settings.scroll_cooldown_ms / 1000,
        )
