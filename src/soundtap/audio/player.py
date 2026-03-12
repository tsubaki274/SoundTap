from __future__ import annotations

import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class AudioPlayer:
    def __init__(self, num_channels: int = 32) -> None:
        self._num_channels = num_channels
        self._pygame: Any | None = None
        self._sound_cache: dict[Path, Any] = {}

    def initialize(self) -> None:
        if self._pygame is not None:
            return

        import pygame

        pygame.mixer.init()
        pygame.mixer.set_num_channels(self._num_channels)
        self._pygame = pygame

    def shutdown(self) -> None:
        if self._pygame is None:
            return

        self._pygame.mixer.stop()
        self._pygame.mixer.quit()
        self._pygame = None
        self._sound_cache.clear()

    def stop_all(self) -> None:
        if self._pygame is None:
            return

        self._pygame.mixer.stop()

    def clear_cache(self) -> None:
        self._sound_cache.clear()

    def play(self, sound_path: Path, volume: float) -> bool:
        self.initialize()

        if self._pygame is None:
            return False

        normalized_path = sound_path.expanduser()
        if not normalized_path.exists():
            logger.warning("Sound file does not exist: %s", normalized_path)
            return False

        try:
            sound = self._load_sound(normalized_path)
        except Exception as exc:
            logger.warning("Failed to load sound %s: %s", normalized_path, exc)
            return False

        channel = sound.play()
        if channel is None:
            channel = self._pygame.mixer.find_channel(force=True)
            if channel is None:
                logger.warning("No audio channel available for %s", normalized_path)
                return False
            channel.play(sound)

        channel.set_volume(max(0.0, min(1.0, volume)))
        return True

    def _load_sound(self, sound_path: Path) -> Any:
        cached_sound = self._sound_cache.get(sound_path)
        if cached_sound is not None:
            return cached_sound

        if self._pygame is None:
            raise RuntimeError("Pygame mixer is not initialized")

        sound = self._pygame.mixer.Sound(str(sound_path))
        self._sound_cache[sound_path] = sound
        return sound
