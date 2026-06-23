#!/usr/bin/env python3
import subprocess
import sys

# Suppress console window popups on Windows (WhisperX/FFmpeg subprocess calls)
# Only apply in PyInstaller exe mode, not in dev
if sys.platform == "win32" and getattr(sys, 'frozen', False):
    subprocess.CREATE_NO_WINDOW = 0x08000000
    original_popen = subprocess.Popen

    def patched_popen(*args, **kwargs):
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        return original_popen(*args, **kwargs)

    subprocess.Popen = patched_popen

import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.splash import create_splash, animate_splash_until

# Enable debug logging (comment out for production)
DEBUG = True

# Fix stdout/stderr when console is disabled (PyInstaller without console)
class NullWriter:
    def write(self, s):
        pass
    def flush(self):
        pass

if sys.stdout is None:
    sys.stdout = NullWriter()
if sys.stderr is None:
    sys.stderr = NullWriter()

def setup_logging():
    """Configure logging to both console and file."""
    log_dir = Path.home() / ".SubXeta"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "subxeta.log"

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # File handler (always enabled, overwrites on each run)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Console handler (for when console is visible)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

setup_logging()

if DEBUG:
    logging.getLogger("ui.main_window.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.subtitle_gen.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.chunks.debug").setLevel(logging.DEBUG)
    logging.getLogger("ui.steps.step2_review.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.transcription.debug").setLevel(logging.DEBUG)


def main():
    app = QApplication(sys.argv)

    # Show the splash immediately, then build the window while it's on screen
    splash, splash_pixmap, splash_start = create_splash(app)

    window = MainWindow()

    # Only fill whatever time remains up to the minimum (no fixed wait in front
    # of the build) — total splash time is max(build_time, min_duration)
    animate_splash_until(app, splash, splash_pixmap, splash_start, min_duration=1.0)

    window.show()
    if splash:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
