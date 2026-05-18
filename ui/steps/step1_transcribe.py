from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import pyqtSignal, QTimer, QRect
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient, QPen
from ui.widgets import DragDropArea


class ShimmerProgressBar(QProgressBar):
    """Progress bar with animated shimmer effect."""

    def __init__(self):
        super().__init__()
        self.shimmer_pos = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_shimmer)

    def start_shimmer(self):
        self.timer.start(30)

    def stop_shimmer(self):
        self.timer.stop()

    def _update_shimmer(self):
        self.shimmer_pos = (self.shimmer_pos + 3) % 100
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.value() > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)

            # Draw shimmer overlay
            rect = self.contentsRect()
            width = rect.width()

            # Shimmer position across the filled portion
            fill_width = (width * self.value()) / self.maximum() if self.maximum() > 0 else 0
            shimmer_x = (fill_width * self.shimmer_pos) / 100

            # Create shimmer gradient, clipped to filled area
            shimmer_left = max(rect.x(), int(shimmer_x - 30))
            shimmer_right = min(int(fill_width), int(shimmer_x + 30))
            if shimmer_left < shimmer_right:
                shimmer_rect = QRect(shimmer_left, rect.y(), shimmer_right - shimmer_left, rect.height())
                gradient = QLinearGradient(shimmer_rect.left(), 0, shimmer_rect.right(), 0)
                gradient.setColorAt(0, QColor(0, 255, 136, 0))
                gradient.setColorAt(0.5, QColor(255, 255, 255, 100))
                gradient.setColorAt(1, QColor(0, 255, 136, 0))

                painter.fillRect(shimmer_rect, gradient)
            painter.end()


class Step1Widget(QGroupBox):
    transcription_started = pyqtSignal(str)  # emits file path

    def __init__(self):
        super().__init__("Step 1 • Transcribe Audio")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        desc = QLabel("Upload an audio or video file to transcribe using WhisperX")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(desc)

        layout.addSpacing(20)

        self.audio_input = DragDropArea("Drag audio/video file here or click to browse")
        self.audio_input.fileSelected.connect(self._on_file_selected)
        layout.addWidget(self.audio_input)

        layout.addSpacing(20)

        self.transcribe_btn = QPushButton("Start Transcription")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setMinimumHeight(48)
        self.transcribe_btn.clicked.connect(self._on_transcribe_clicked)
        layout.addWidget(self.transcribe_btn)

        self.progress_bar = ShimmerProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def _on_file_selected(self, file_path):
        self.transcribe_btn.setEnabled(True)

    def _on_transcribe_clicked(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.start_shimmer()
        self.transcription_started.emit(self.audio_input.text())

    def stop_shimmer(self):
        """Call this when transcription completes."""
        self.progress_bar.stop_shimmer()
