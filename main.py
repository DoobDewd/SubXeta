#!/usr/bin/env python3
"""
Subtitle Comp App - Modern sidebar + main content layout.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.styles import get_stylesheet
from ui.widgets import DragDropArea
from ui.tab_bar import TabBar


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
        layout.addWidget(self.step1_content)

        # Step 2: Review & Generate
        self.step2_content = self.create_step2_content()
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
        self.transcribe_btn = QPushButton("▶ Start Transcription")
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
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        chunks_widget = QWidget()
        self.chunks_layout = QVBoxLayout()
        self.chunks_layout.setSpacing(12)
        chunks_widget.setLayout(self.chunks_layout)
        scroll.setWidget(chunks_widget)
        layout.addWidget(scroll)

        layout.addSpacing(20)

        # Generate button
        self.generate_btn = QPushButton("✨ Generate Comp")
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
        self.show_step(2)
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
        for timestamp, text in chunks:
            card = self.create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)

        self.chunks_layout.addStretch()
        self.generate_btn.setEnabled(True)

    def create_chunk_card(self, timestamp, text):
        """Create a chunk edit card."""
        card = QGroupBox()
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
        text_edit.setText(text)
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
        return card

    def start_generation(self):
        """Start comp generation."""
        self.generate_progress.setVisible(True)
        self.result_label.setText("✓ Comp generated! Check the subs folder.")

    def show_step(self, step):
        """Show a specific step and hide others."""
        self.step1_content.setVisible(step == 1)
        self.step2_content.setVisible(step == 2)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
