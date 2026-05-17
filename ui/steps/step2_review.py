from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QScrollArea, QWidget, QTextEdit
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter
from ui.animations import CRTAnimatedMixin, TypingAnimator


class ChunkCard(QGroupBox, CRTAnimatedMixin):
    def __init__(self):
        super().__init__()
        self._init_crt_effect()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        self._draw_crt_effect(painter, self.rect())
        painter.end()


class Step2Widget(QGroupBox):
    generation_started = pyqtSignal()

    def __init__(self):
        super().__init__("Step 2 • Review & Generate")
        self._typing_animator = TypingAnimator(char_delay_ms=25)
        self._chunks = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        self.status_label = QLabel("Waiting for transcription...")
        self.status_label.setStyleSheet("color: #e0e0e0; background-color: transparent; padding: 0px 12px;")
        layout.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(350)
        chunks_widget = QWidget()
        chunks_widget.setStyleSheet("QWidget { background-color: #191e1c; }")
        self.chunks_layout = QVBoxLayout()
        self.chunks_layout.setSpacing(12)
        chunks_widget.setLayout(self.chunks_layout)
        scroll.setWidget(chunks_widget)
        layout.addWidget(scroll)

        layout.addSpacing(20)

        self.generate_btn = QPushButton("Generate Comp")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setMinimumHeight(48)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        layout.addWidget(self.generate_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet("background-color: transparent; color: #00ff88; font-weight: bold;")
        layout.addWidget(self.result_label)

        self.setLayout(layout)

    def set_status(self, text):
        self.status_label.setText(text)

    def populate_chunks(self, chunks):
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._chunks = []
        typing_targets = []
        for timestamp, text in chunks:
            card, text_edit = self._create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)
            typing_targets.append((text_edit, text))
            self._chunks.append((timestamp, text_edit))

        self.chunks_layout.addStretch()
        self.generate_btn.setEnabled(True)
        self._typing_animator.animate_sequence(typing_targets)

    def restart_typing(self):
        self._typing_animator.restart()

    def _create_chunk_card(self, timestamp, text):
        card = ChunkCard()
        card.setStyleSheet("""
            QGroupBox {
                border: 1px solid #00ff88;
                border-radius: 6px;
                margin: 0px;
                padding: 12px;
            }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("color: #00ff88; font-weight: 600; font-size: 11px; background-color: transparent;")
        layout.addWidget(timestamp_label)

        text_edit = QTextEdit()
        text_edit.setMinimumHeight(60)
        text_edit.setMaximumHeight(100)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid rgba(0, 255, 136, 0.3);
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }
            QTextEdit:focus {
                background-color: #1f1f1f;
                border: 2px solid #00ffaa;
            }
        """)
        layout.addWidget(text_edit)

        card.setLayout(layout)
        return card, text_edit

    def get_edited_chunks(self):
        """Get the currently edited chunks."""
        edited = []
        for timestamp, text_edit in self._chunks:
            edited.append((timestamp, text_edit.toPlainText()))
        return edited

    def _on_generate_clicked(self):
        self.progress_bar.setVisible(True)
        self.generate_btn.setEnabled(False)
        self.generation_started.emit()

