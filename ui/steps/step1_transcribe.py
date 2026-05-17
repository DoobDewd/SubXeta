from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from ui.widgets import DragDropArea


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

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def _on_file_selected(self, file_path):
        self.transcribe_btn.setEnabled(True)

    def _on_transcribe_clicked(self):
        self.progress_bar.setVisible(True)
        self.transcription_started.emit(self.audio_input.text())
