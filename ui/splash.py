"""Splash screen with animated spinner."""
import time
from pathlib import Path
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtGui import QPixmap, QFont, QColor, QPainter
from PyQt6.QtCore import Qt, QRect

from ui import theme


def show_splash_with_spinner(app, duration=2.0):
    """Show splash screen with animated spinner at bottom left.

    Args:
        app: QApplication instance
        duration: How long to show splash (seconds)

    Returns:
        QSplashScreen instance or None if splash.png not found
    """
    # Try multiple paths for splash.png (dev and exe)
    possible_paths = [
        Path(__file__).parent.parent / "splash.png",  # Development
        Path.cwd() / "splash.png",  # Exe root
    ]

    splash_path = None
    for path in possible_paths:
        if path.exists():
            splash_path = path
            break

    if splash_path is None:
        return None

    pixmap = QPixmap(str(splash_path))
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()

    font = QFont()
    font.setPointSize(20)
    font.setBold(True)

    color = QColor(*theme.GREEN_RGB)
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    start = time.time()
    i = 0
    while time.time() - start < duration:
        frame_pixmap = pixmap.copy()
        painter = QPainter(frame_pixmap)
        painter.setFont(font)

        # Draw glow effect (multiple offset passes with transparency)
        for offset in range(4, 0, -1):
            alpha = int(80 * (1 - offset / 4))
            glow = QColor(*theme.GREEN_RGB, alpha)
            painter.setPen(glow)
            painter.drawText(
                QRect(20 + offset, frame_pixmap.height() - 40 + offset, 100, 40),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                spinner[i % len(spinner)]
            )

        # Draw main spinner text
        painter.setPen(color)
        painter.drawText(
            QRect(20, frame_pixmap.height() - 40, 100, 40),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            spinner[i % len(spinner)]
        )
        painter.end()

        splash.setPixmap(frame_pixmap)
        app.processEvents()
        time.sleep(0.1)
        i += 1

    return splash
