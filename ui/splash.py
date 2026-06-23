"""Splash screen with animated spinner."""
import time
from pathlib import Path
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter
from PyQt6.QtCore import Qt, QRect

from ui import theme


_SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']


def _paint_spinner_frame(splash, pixmap, frame):
    """Draw one spinner frame (with green glow) onto the splash."""
    font = QFont()
    font.setPointSize(20)
    font.setBold(True)
    glyph = _SPINNER[frame % len(_SPINNER)]

    frame_pixmap = pixmap.copy()
    painter = QPainter(frame_pixmap)
    painter.setFont(font)

    # Glow (offset passes with transparency)
    for offset in range(4, 0, -1):
        alpha = int(80 * (1 - offset / 4))
        painter.setPen(QColor(*theme.GREEN_RGB, alpha))
        painter.drawText(
            QRect(20 + offset, frame_pixmap.height() - 40 + offset, 100, 40),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            glyph,
        )

    # Main spinner glyph
    painter.setPen(QColor(*theme.GREEN_RGB))
    painter.drawText(
        QRect(20, frame_pixmap.height() - 40, 100, 40),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        glyph,
    )
    painter.end()
    splash.setPixmap(frame_pixmap)


def create_splash(app):
    """Create and show the splash screen immediately (first spinner frame painted),
    so it's on screen while the main window builds.

    Returns (splash, pixmap, start_time), or (None, None, None) if splash.png is missing.
    """
    possible_paths = [
        Path(__file__).parent.parent / "splash.png",  # Development
        Path.cwd() / "splash.png",  # Exe root
    ]
    splash_path = next((p for p in possible_paths if p.exists()), None)
    if splash_path is None:
        return None, None, None

    pixmap = QPixmap(str(splash_path))
    splash = QSplashScreen(pixmap)
    splash.show()
    _paint_spinner_frame(splash, pixmap, 0)
    app.processEvents()
    return splash, pixmap, time.time()


def animate_splash_until(app, splash, pixmap, start_time, min_duration=1.0):
    """Keep animating the spinner until min_duration has elapsed since start_time.

    Called after the main window is built, so the splash only fills whatever time
    remains up to min_duration — total splash time is max(build_time, min_duration)
    instead of a fixed wait added in front of the build.
    """
    if splash is None:
        return
    frame = 1
    while time.time() - start_time < min_duration:
        _paint_spinner_frame(splash, pixmap, frame)
        app.processEvents()
        time.sleep(0.1)
        frame += 1
