#!/usr/bin/env python3
"""
Subtitle Comp App - Modern sidebar + main content layout.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QGroupBox, QScrollArea, QFrame, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPalette
import random

from ui.styles import get_stylesheet
from ui.widgets import DragDropArea, ScanlineOverlay, CRTEffect
from ui.tab_bar import TabBar


class ChunkCard(QGroupBox):
    """Chunk card with CRT scanline background pattern."""
    def __init__(self):
        super().__init__()
        self._crt_effect = CRTEffect()
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self):
        self._crt_effect.tick()
        self.update()

    def paintEvent(self, event):
        # Call parent paintEvent first to draw the groupbox and children
        super().paintEvent(event)

        painter = QPainter(self)
        self._crt_effect.draw(painter, self.rect())
        painter.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Comp App")
        self.setGeometry(100, 100, 1200, 800)

        # Main container
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)

        # Navigation bar with padding
        nav_container = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(40, 12, 40, 0)
        nav_layout.setSpacing(0)

        self.tab_bar = TabBar()
        self.tab_bar.tab_changed.connect(self.on_tab_changed)
        nav_layout.addWidget(self.tab_bar)

        nav_container.setLayout(nav_layout)
        nav_container.setStyleSheet("background-color: #1a1a1a;")
        main_layout.addWidget(nav_container)

        # Content area
        content = self.create_content_area()
        main_layout.addWidget(content, 1)

        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())

    def on_tab_changed(self, step):
        self.show_step(step)

    def create_content_area(self):
        """Create main content area that changes per step."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)

        # Step 1: Transcribe
        self.step1_content = self.create_step1_content()
        self.step1_effect = QGraphicsOpacityEffect()
        self.step1_effect.setOpacity(1.0)
        self.step1_content.setGraphicsEffect(self.step1_effect)
        layout.addWidget(self.step1_content)

        # Step 2: Review & Generate
        self.step2_content = self.create_step2_content()
        self.step2_effect = QGraphicsOpacityEffect()
        self.step2_effect.setOpacity(0.0)
        self.step2_content.setGraphicsEffect(self.step2_effect)
        self.step2_content.setVisible(False)
        layout.addWidget(self.step2_content)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        return scroll

    def create_step1_content(self):
        """Step 1: Transcribe Audio."""
        group = QGroupBox("Step 1 • Transcribe Audio")
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Description
        desc = QLabel("Upload an audio or video file to transcribe using WhisperX")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(desc)

        layout.addSpacing(20)

        # Upload box
        self.audio_input = DragDropArea("Drag audio/video file here or click to browse")
        layout.addWidget(self.audio_input)

        layout.addSpacing(20)

        # Transcribe button
        self.transcribe_btn = QPushButton("Start Transcription")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setMinimumHeight(48)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.audio_input.fileSelected.connect(self.on_audio_selected)
        layout.addWidget(self.transcribe_btn)

        # Progress bar
        self.transcribe_progress = QProgressBar()
        self.transcribe_progress.setVisible(False)
        layout.addWidget(self.transcribe_progress)

        group.setLayout(layout)
        return group

    def create_step2_content(self):
        """Step 2: Review & Edit Chunks, then Generate."""
        group = QGroupBox("Step 2 • Review & Generate")
        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Status message
        self.review_status = QLabel("Waiting for transcription...")
        self.review_status.setStyleSheet("color: #e0e0e0; background-color: transparent; padding: 0px 12px;")
        layout.addWidget(self.review_status)

        # Scroll area for chunks
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(350)
        chunks_widget = QWidget()
        # Use the calculated blended color: rgba(0,255,136,0.02) on #1a1a1a
        chunks_widget.setStyleSheet("""
            QWidget {
                background-color: #191e1c;
            }
        """)
        self.chunks_layout = QVBoxLayout()
        self.chunks_layout.setSpacing(12)
        chunks_widget.setLayout(self.chunks_layout)
        scroll.setWidget(chunks_widget)

        layout.addWidget(scroll)

        layout.addSpacing(20)

        # Generate button
        self.generate_btn = QPushButton("Generate Comp")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setMinimumHeight(48)
        self.generate_btn.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_btn)

        # Progress bar
        self.generate_progress = QProgressBar()
        self.generate_progress.setVisible(False)
        layout.addWidget(self.generate_progress)

        # Result
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("background-color: transparent; color: #00ff88; font-weight: bold;")
        layout.addWidget(self.result_label)

        group.setLayout(layout)
        return group

    def on_audio_selected(self, file_path):
        self.transcribe_btn.setEnabled(True)

    def start_transcription(self):
        self.transcribe_progress.setVisible(True)
        self.review_status.setText("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        self.tab_bar.enable_step(2, on_complete=lambda: self.show_step(2))
        self.populate_chunks_table()

    def populate_chunks_table(self):
        """Populate the chunks table with placeholder data."""
        chunks = [
            ("0:00.000", "Hello world"),
            ("0:02.500", "This is a test"),
        ]

        # Clear previous chunks
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create chunk cards
        typing_targets = []
        for timestamp, text in chunks:
            card, text_edit = self.create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)
            typing_targets.append((text_edit, text))

        self.chunks_layout.addStretch()
        self.generate_btn.setEnabled(True)
        self._start_typing_sequence(typing_targets)

    def create_chunk_card(self, timestamp, text):
        """Create a chunk edit card."""
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

        # Timestamp
        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("color: #00ff88; font-weight: 600; font-size: 11px; background-color: transparent;")
        layout.addWidget(timestamp_label)

        # Text edit
        text_edit = QTextEdit()
        text_edit.setText("")
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

    def start_generation(self):
        """Start comp generation."""
        self.generate_progress.setVisible(True)
        self.result_label.setText("✓ Comp generated! Check the subs folder.")

    def _start_typing_sequence(self, targets):
        """Start typing animation for chunks sequentially."""
        if not targets:
            return
        self._typing_targets = targets
        self._typing_index = 0
        self._typing_char_index = 0
        self._typing_timer = QTimer()
        self._typing_timer.setInterval(25)
        self._typing_timer.timeout.connect(self._typing_tick)
        self._typing_timer.start()

    def _restart_typing_animation(self):
        """Restart typing animation from the beginning."""
        if not hasattr(self, '_typing_targets') or not self._typing_targets:
            return
        # Stop current animation
        if hasattr(self, '_typing_timer') and self._typing_timer.isActive():
            self._typing_timer.stop()
        # Clear all text
        for text_edit, _ in self._typing_targets:
            text_edit.setText("")
        # Restart from beginning
        self._typing_index = 0
        self._typing_char_index = 0
        self._typing_timer.start()

    def _typing_tick(self):
        """Advance typing animation by one character."""
        if self._typing_index >= len(self._typing_targets):
            self._typing_timer.stop()
            return
        text_edit, full_text = self._typing_targets[self._typing_index]
        if self._typing_char_index < len(full_text):
            text_edit.setText(full_text[:self._typing_char_index + 1])
            self._typing_char_index += 1
        else:
            self._typing_index += 1
            self._typing_char_index = 0

    def show_step(self, step):
        """Show a specific step with smooth fade transition."""
        self.tab_bar.set_active(step, animate=True)

        outgoing = self.step1_content if step == 2 else self.step2_content
        incoming = self.step2_content if step == 2 else self.step1_content
        out_effect = self.step1_effect if step == 2 else self.step2_effect
        in_effect = self.step2_effect if step == 2 else self.step1_effect

        if not outgoing.isVisible():
            incoming.setVisible(True)
            in_effect.setOpacity(1.0)
            if step == 2:
                self._restart_typing_animation()
            return

        fade_out = QPropertyAnimation(out_effect, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_fade_out_done():
            outgoing.setVisible(False)
            incoming.setVisible(True)
            fade_in = QPropertyAnimation(in_effect, b"opacity")
            fade_in.setDuration(150)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InCubic)
            fade_in.start()
            self._fade_in_anim = fade_in
            if step == 2:
                self._restart_typing_animation()

        fade_out.finished.connect(on_fade_out_done)
        self._fade_out_anim = fade_out
        fade_out.start()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
