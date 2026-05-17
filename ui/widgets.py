"""Custom widgets for the Subtitle Comp App."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QCursor, QPainter, QColor


class DragDropArea(QWidget):
    fileSelected = pyqtSignal(str)

    def __init__(self, placeholder_text="Drag files here"):
        super().__init__()
        self.file_path = None
        self.placeholder_text = placeholder_text

        layout = QVBoxLayout()
        self.label = QLabel(placeholder_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setMinimumHeight(140)

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
                                background-color: rgba(0, 255, 136, 0.1);
            }
        """)

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


class ScanlineOverlay(QWidget):
    """CRT scanline effect overlay (static horizontal lines)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._flicker = 0
        self._timer = QTimer(self)
        self._timer.setInterval(100)  # Subtle flicker every 100ms
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        """Update flicker intensity."""
        self._flicker = (self._flicker + 1) % 3  # Cycle through 0, 1, 2
        self.update()

    def paintEvent(self, event):
        """Draw CRT-style horizontal scanlines."""
        painter = QPainter(self)
        h = self.height()
        w = self.width()

        # Draw horizontal lines spaced 2 pixels apart (classic CRT look)
        for y in range(0, h, 2):
            # Vary opacity slightly for flicker effect
            base_alpha = 15
            flicker_alpha = base_alpha + (self._flicker * 2)
            color = QColor(0, 255, 136, flicker_alpha)
            painter.setPen(color)
            painter.drawLine(0, y, w, y)

        painter.end()
