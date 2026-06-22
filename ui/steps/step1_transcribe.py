from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, QTimer, QRect, Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QColor, QLinearGradient
from ui.widgets import DragDropArea
from ui import theme


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
                gradient.setColorAt(0, QColor(*theme.GREEN_RGB, 0))
                gradient.setColorAt(0.5, QColor(255, 255, 255, 125))
                gradient.setColorAt(1, QColor(*theme.GREEN_RGB, 0))

                painter.fillRect(shimmer_rect, gradient)
            painter.end()


class Step1Widget(QGroupBox):
    transcription_started = pyqtSignal(str)  # emits file path

    def __init__(self):
        super().__init__("Step 1 • Transcribe Audio")
        self._build_ui()
        self._ellipsis_timer = QTimer()
        self._ellipsis_timer.timeout.connect(self._update_ellipsis)
        self._ellipsis_count = 0
        self._current_stage_name = ""

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        desc = QLabel("Upload an audio or video file to transcribe.")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet(f"color: {theme.TEXT}; background-color: transparent;")
        layout.addWidget(desc)

        layout.addSpacing(20)

        self.audio_input = DragDropArea("Drag audio/video file here or click to browse")
        self.audio_input.fileSelected.connect(self._on_file_selected)
        layout.addWidget(self.audio_input)

        layout.addSpacing(20)

        self.transcribe_btn = QPushButton("Start Transcription")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setFixedHeight(56)
        self.transcribe_btn.setMaximumWidth(300)
        self.transcribe_btn.clicked.connect(self._on_transcribe_clicked)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.transcribe_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addStretch()
        layout.addLayout(btn_layout, stretch=0)

        self.progress_bar = ShimmerProgressBar()
        self.progress_bar.setVisible(False)
        self._progress_anim = None
        layout.addWidget(self.progress_bar)

        self.progress_label = QLabel("0%")
        self.progress_label.setStyleSheet(f"color: {theme.GREEN}; background-color: transparent; font-weight: bold; font-family: monospace;")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)

        self.setLayout(layout)

    def _on_file_selected(self, file_path):
        self.transcribe_btn.setEnabled(True)

    def _on_transcribe_clicked(self):
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        self.progress_bar.start_shimmer()
        self.transcription_started.emit(self.audio_input.text())

    def _update_progress_label(self, value):
        """Update the progress percentage label."""
        self.progress_label.setText(f"{value}%")

    def set_progress_with_stage(self, stage_name: str, percentage: int):
        """Update progress bar with stage name and percentage (0-100 per stage)."""
        # Check if this is an indeterminate stage (no real progress tracking)
        is_indeterminate = stage_name == "Transcribing audio"

        if is_indeterminate:
            # For indeterminate stages, show animated ellipsis and full progress bar
            self._current_stage_name = stage_name
            if percentage == 0:
                # Starting indeterminate stage
                self._ellipsis_count = 0
                self._ellipsis_timer.start(300)  # Update ellipsis every 300ms
                self.set_progress_smoothly(100)
            elif percentage == 100:
                # Completing indeterminate stage
                self._ellipsis_timer.stop()
                self.progress_label.setText(f"{stage_name}... Complete")
        else:
            # For determinate stages, show normal progress with percentage
            self._ellipsis_timer.stop()
            self._current_stage_name = ""
            self.progress_label.setText(f"{stage_name}... {percentage}%")
            self.set_progress_smoothly(percentage)

    def set_progress_smoothly(self, target_value):
        """Smoothly animate progress bar to target value."""
        current_value = self.progress_bar.value()
        if current_value == target_value:
            return

        if self._progress_anim and self._progress_anim.state() == QPropertyAnimation.State.Running:
            self._progress_anim.stop()

        self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
        self._progress_anim.setDuration(250)
        self._progress_anim.setStartValue(current_value)
        self._progress_anim.setEndValue(target_value)
        self._progress_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._progress_anim.start()

    def _update_ellipsis(self):
        """Animate ellipsis (. → .. → ...) for indeterminate progress."""
        self._ellipsis_count = (self._ellipsis_count + 1) % 4
        dots = "." * self._ellipsis_count if self._ellipsis_count > 0 else "."
        # Pad with spaces to keep text width constant (no shifting)
        padded_dots = dots.ljust(3)
        self.progress_label.setText(f"{self._current_stage_name}{padded_dots}")

    def stop_shimmer(self):
        """Call this when transcription completes."""
        self._ellipsis_timer.stop()
        self.progress_bar.stop_shimmer()
