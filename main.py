#!/usr/bin/env python3
import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Enable debug logging (comment out for production)
DEBUG = True

if DEBUG:
    logging.getLogger("ui.main_window.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.subtitle_gen.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.chunks.debug").setLevel(logging.DEBUG)
    logging.getLogger("ui.steps.step2_review.debug").setLevel(logging.DEBUG)
    logging.getLogger("core.transcription.debug").setLevel(logging.DEBUG)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
