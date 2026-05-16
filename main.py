#!/usr/bin/env python3
"""
Subtitle Comp App - Main window and application entry point.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QProgressBar, QTextEdit,
    QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.styles import get_stylesheet
from ui.widgets import DragDropArea


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Comp App")
        self.setGeometry(100, 100, 900, 1000)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()

        # Step 1: Transcribe Audio
        self.step1_group = self.create_step1()
        scroll_layout.addWidget(self.step1_group)
        scroll_layout.addSpacing(32)

        # Step 2: Review & Edit Chunks
        self.step2_group = self.create_step2()
        self.step2_group.setVisible(False)
        scroll_layout.addWidget(self.step2_group)
        scroll_layout.addSpacing(32)

        # Step 3: Generate Comp
        self.step3_group = self.create_step3()
        self.step3_group.setVisible(False)
        scroll_layout.addWidget(self.step3_group)

        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)

        main_layout.addWidget(scroll)

        # Apply stylesheet
        self.setStyleSheet(get_stylesheet())

    def create_step1(self):
        group = QGroupBox("Step 1/3 • Transcribe Audio")
        layout = QVBoxLayout()

        # File selection
        self.audio_input = DragDropArea("Drag audio/video file here or click to browse")
        self.audio_input.fileSelected.connect(self.on_audio_selected)
        layout.addWidget(self.audio_input)

        # Transcribe button
        self.transcribe_btn = QPushButton("▶ Transcribe Audio")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setMaximumWidth(220)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.transcribe_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.transcribe_progress = QProgressBar()
        self.transcribe_progress.setVisible(False)
        layout.addWidget(self.transcribe_progress)

        group.setLayout(layout)
        return group

    def create_step2(self):
        group = QGroupBox("Step 2/3 • Review & Edit Chunks")
        main_layout = QVBoxLayout()

        # Status
        self.review_status = QLabel("Waiting for transcription...")
        self.review_status.setStyleSheet("background-color: transparent; margin: 0px; padding: 0px 12px;")
        main_layout.addWidget(self.review_status)

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
        main_layout.addWidget(scroll)

        group.setLayout(main_layout)
        return group

    def create_step3(self):
        group = QGroupBox("Step 3/3 • Generate Comp")
        layout = QVBoxLayout()

        # Generate button
        self.generate_btn = QPushButton("✨ Generate Comp")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.start_generation)
        self.generate_btn.setMaximumWidth(220)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.generate_progress = QProgressBar()
        self.generate_progress.setVisible(False)
        layout.addWidget(self.generate_progress)

        # Result
        self.result_label = QLabel("")
        self.result_label.setStyleSheet("background-color: transparent;")
        layout.addWidget(self.result_label)

        group.setLayout(layout)
        return group

    def on_audio_selected(self, file_path):
        self.transcribe_btn.setEnabled(True)

    def start_transcription(self):
        self.transcribe_progress.setVisible(True)
        # Placeholder for actual transcription
        self.step1_group.setTitle("✓ Step 1/3 • Transcribe Audio")
        self.review_status.setText("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        self.step2_group.setVisible(True)
        self.populate_chunks_table()

    def populate_chunks_table(self):
        # Placeholder data
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
        self.step2_group.setTitle("✓ Step 2/3 • Review & Edit Chunks")
        self.step3_group.setVisible(True)
        self.generate_btn.setEnabled(True)

    def create_chunk_card(self, timestamp, text):
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
                border: 1px solid #00ff88;
            }
        """)
        layout.addWidget(text_edit)

        card.setLayout(layout)
        return card

    def start_generation(self):
        self.generate_progress.setVisible(True)
        # Placeholder for actual generation
        self.step3_group.setTitle("✓ Step 3/3 • Generate Comp")
        self.result_label.setText("✓ Comp generated! Check the subs folder.")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
