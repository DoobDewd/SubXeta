"""Custom widgets for the Subtitle Comp App."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QPainter, QColor
import random


class CRTEffect:
    """Reusable CRT scanline animation effect."""

    def __init__(self):
        self._scan_offset = 0.0
        self._frame = 0
        self._sweep_active = False
        self._sweep_progress = 0.0
        self._frames_until_next_sweep = 0

    def tick(self):
        """Update animation state."""
        self._scan_offset += 0.08
        self._frame += 1
        if self._scan_offset >= 2.0:
            self._scan_offset -= 2.0

        # Manage sweep line animation
        if self._sweep_active:
            self._sweep_progress += 0.08
            if self._sweep_progress >= 1.0:
                self._sweep_active = False
                self._frames_until_next_sweep = random.randint(40, 120)
        else:
            self._frames_until_next_sweep -= 1
            if self._frames_until_next_sweep <= 0:
                self._sweep_active = True
                self._sweep_progress = 0.0

    def draw(self, painter, rect):
        """Draw the CRT effect on the given rect."""
        h = rect.height()
        w = rect.width()

        # Scanline frequency
        freq = 6.5

        # Fast frame-based flicker for CRT effect
        flicker_val = (self._frame % 2) / 1.0
        if flicker_val > 1.0:
            flicker_val = 2.0 - flicker_val

        # Create scanline pattern
        for y in range(h):
            frac_val = (y * freq + self._scan_offset) % 1.0
            scanline_val = abs(frac_val - 0.5) * 2.0
            alpha = int(scanline_val * 35)
            alpha = int(alpha * (0.85 + flicker_val * 0.15))

            color = QColor(0, 255, 136, alpha)
            painter.setPen(color)
            painter.drawLine(rect.x(), rect.y() + y, rect.x() + w, rect.y() + y)

        # Draw sweep line when active
        if self._sweep_active:
            sweep_y = int(self._sweep_progress * h)
            if 0 <= sweep_y < h:
                sweep_color = QColor(0, 255, 136, 60)
                painter.setPen(sweep_color)
                painter.drawLine(rect.x(), rect.y() + sweep_y, rect.x() + w, rect.y() + sweep_y)

    def start_sweep(self):
        """Start a sweep animation."""
        self._sweep_active = True
        self._sweep_progress = 0.0


class DragDropArea(QWidget):
    fileSelected = pyqtSignal(str)

    def __init__(self, placeholder_text="Drag files here"):
        super().__init__()
        self.file_path = None
        self.placeholder_text = placeholder_text
        self._is_hovering = False
        self._crt_effect = CRTEffect()

        layout = QVBoxLayout()
        self.label = QLabel(placeholder_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                outline: none;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        # Start animation timer
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        if self._is_hovering:
            self._crt_effect.tick()
            self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #ff00ff;
                    border-radius: 5px;
                    padding: 40px;
                    color: #ff00ff;
                }
            """)

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
            }
        """)

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_path = files[0]
            self.setText(self.file_path)
            self.fileSelected.emit(self.file_path)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
            }
        """)

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.file_path or ""

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px solid #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                background-color: transparent;
            }
        """)
        self._is_hovering = True
        self._crt_effect.start_sweep()

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                            }
        """)
        self._is_hovering = False

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select audio or video file",
            "",
            "Audio/Video Files (*.mp3 *.wav *.m4a *.mp4 *.mov *.avi);;All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            self.setText(file_path)
            self.fileSelected.emit(file_path)

    def paintEvent(self, event):
        # Call parent paintEvent first to draw children
        super().paintEvent(event)

        # Only draw scanline effect when hovering
        if not self._is_hovering:
            return

        painter = QPainter(self)
        label_rect = self.label.geometry()
        self._crt_effect.draw(painter, label_rect)
        painter.end()
