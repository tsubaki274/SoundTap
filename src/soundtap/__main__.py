from __future__ import annotations

import logging

from soundtap.app import SoundTapApp


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> int:
    configure_logging()
    app = SoundTapApp()
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
