from __future__ import annotations

from typing import Any


class TrayIconApp:
    def __init__(self, app: Any) -> None:
        self._app = app

    def run(self) -> None:
        from PIL import Image, ImageDraw
        from pystray import Icon, Menu, MenuItem

        def create_image() -> Any:
            image = Image.new("RGB", (64, 64), "#1f2933")
            draw = ImageDraw.Draw(image)
            draw.ellipse((10, 10, 54, 54), fill="#43aa8b")
            draw.rectangle((28, 18, 36, 46), fill="#f4f1de")
            draw.rectangle((18, 28, 46, 36), fill="#f4f1de")
            return image

        def noop(_icon: Any, _item: Any) -> None:
            return None

        def start(icon: Any, _item: Any) -> None:
            started = self._app.start()
            icon.update_menu()
            if started:
                icon.notify("SoundTap started")

        def stop(icon: Any, _item: Any) -> None:
            self._app.stop()
            icon.update_menu()
            icon.notify("SoundTap stopped")

        def toggle_mute(icon: Any, _item: Any) -> None:
            muted = self._app.toggle_mute()
            icon.update_menu()
            icon.notify("SoundTap muted" if muted else "SoundTap unmuted")

        def reload_config(icon: Any, _item: Any) -> None:
            self._app.reload_settings()
            icon.notify(f"Reloaded {self._app.config_path}")

        def open_config_dir(_icon: Any, _item: Any) -> None:
            self._app.open_config_dir()

        def quit_app(icon: Any, _item: Any) -> None:
            self._app.shutdown()
            icon.stop()

        menu = Menu(
            MenuItem(
                "監視中", noop, checked=lambda item: self._app.is_running, enabled=False
            ),
            MenuItem(
                "ミュート",
                toggle_mute,
                checked=lambda item: self._app.is_muted,
            ),
            MenuItem("開始", start),
            MenuItem("停止", stop),
            MenuItem("設定を再読み込み", reload_config),
            MenuItem("設定フォルダを開く", open_config_dir),
            MenuItem("終了", quit_app),
        )

        def setup(tray_icon: Any) -> None:
            tray_icon.visible = True
            self._app.start()

        icon = Icon("SoundTap", create_image(), "SoundTap", menu)
        icon.run(setup=setup)
