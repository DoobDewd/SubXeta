import logging
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QScrollArea, QWidget, QTextEdit, QHBoxLayout
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QFont
from ui.animations import CRTAnimatedMixin, TypingAnimator

debug_logger = logging.getLogger(f"{__name__}.debug")


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
        self._original_texts = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)

        desc = QLabel("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(desc)

        layout.addSpacing(20)

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
        self.generate_btn.setFixedHeight(56)
        self.generate_btn.setMaximumWidth(300)
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addStretch()
        layout.addLayout(btn_layout, stretch=0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.result_label = QLabel("")
        self.result_label.setStyleSheet("background-color: transparent; color: #00ff88; font-weight: bold;")
        layout.addWidget(self.result_label)

        layout.addStretch()
        self.setLayout(layout)

    def set_status(self, text):
        self.status_label.setText(text)

    def populate_chunks(self, chunks):
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._chunks = []
        self._original_texts = []
        self._full_chunk_texts = []
        typing_targets = []
        for timestamp, text in chunks:
            card, text_edit = self._create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)
            typing_targets.append((text_edit, text))
            self._chunks.append((timestamp, text_edit))
            self._original_texts.append((timestamp, text))
            self._full_chunk_texts.append(text)

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
        """Get the currently edited chunks and track which were actually edited."""
        edited = []
        edited_flags = []
        debug_logger.debug(f"Detecting edits in {len(self._chunks)} chunks")

        for idx, (timestamp, text_edit) in enumerate(self._chunks):
            current_text = text_edit.toPlainText()
            original_text = self._full_chunk_texts[idx] if idx < len(self._full_chunk_texts) else ""

            if not current_text:
                current_text = original_text

            was_edited = current_text != original_text

            if was_edited:
                debug_logger.debug(f"  Chunk {idx} [EDITED]:")
                debug_logger.debug(f"    Original: {original_text[:80]}...")
                debug_logger.debug(f"    Current:  {current_text[:80]}...")
            else:
                debug_logger.debug(f"  Chunk {idx} [UNEDITED]")

            edited.append((timestamp, current_text))
            edited_flags.append(was_edited)

        edit_count = sum(edited_flags)
        debug_logger.debug(f"Edit detection complete: {edit_count}/{len(edited_flags)} chunks were edited")

        # Store flags for later use in main_window
        self._edited_flags = edited_flags
        return edited

    def get_edited_flags(self):
        """Get which chunks were actually edited."""
        return getattr(self, '_edited_flags', [])

    def _on_generate_clicked(self):
        self.progress_bar.setVisible(True)
        self.generate_btn.setEnabled(False)
        self.generation_started.emit()

