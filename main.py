#!/usr/bin/env python3
import sys
import logging
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.splash import show_splash_with_spinner

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

    # Show splash screen
    splash = show_splash_with_spinner(app, duration=2.0)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Hide splash
    if splash:
        splash.finish(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
