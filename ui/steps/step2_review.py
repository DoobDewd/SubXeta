import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QScrollArea, QWidget, QTextEdit, QHBoxLayout, QFileDialog,
    QDialog, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QSize
from PyQt6.QtGui import QPainter, QFont
from ui.animations import CRTAnimatedMixin, TypingAnimator
from ui import theme
from ui.icons import icon_from_svg
from core.models import Word

debug_logger = logging.getLogger(f"{__name__}.debug")


@dataclass
class ChunkItem:
    """All per-chunk state in one place (replaces the old parallel lists).

    ``original_text`` is the baseline used for edit-detection and click-to-fill.
    ``words`` holds the ``List[List[Word]]`` structure and is only set for
    manually added chunks (transcribed chunks keep their word data in
    MainWindow's ``_original_chunks``).
    """
    timestamp: str                       # start time as a string key, e.g. "1.234"
    original_text: str                   # initial text (edit-detection baseline)
    text_edit: QTextEdit                 # the editable widget
    card: QGroupBox                      # the card container widget
    is_manual: bool = False              # manually added vs transcribed
    words: Optional[List[List[Word]]] = None  # word structure, manual chunks only


class AddChunkDialog(QDialog):
    def __init__(self, parent=None, start_time=None, end_time=None):
        super().__init__(parent)
        self.setWindowTitle("Add Chunk")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._prefilled_start = start_time
        self._prefilled_end = end_time
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        start_label = QLabel("Start Time (seconds):")
        start_label.setStyleSheet(f"color: {theme.TEXT};")
        layout.addWidget(start_label)
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setMinimum(0.0)
        self.start_spin.setMaximum(9999.99)
        self.start_spin.setDecimals(2)
        self.start_spin.setValue(self._prefilled_start if self._prefilled_start is not None else 0.0)
        layout.addWidget(self.start_spin)

        end_label = QLabel("End Time (seconds):")
        end_label.setStyleSheet(f"color: {theme.TEXT};")
        layout.addWidget(end_label)
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setMinimum(0.0)
        self.end_spin.setMaximum(9999.99)
        self.end_spin.setDecimals(2)
        self.end_spin.setValue(self._prefilled_end if self._prefilled_end is not None else 1.0)
        layout.addWidget(self.end_spin)

        text_label = QLabel("Text:")
        text_label.setStyleSheet(f"color: {theme.TEXT};")
        layout.addWidget(text_label)
        self.text_edit = QTextEdit()
        self.text_edit.setMinimumHeight(80)
        layout.addWidget(self.text_edit)

        button_layout = QHBoxLayout()
        ok_btn = QPushButton("Add")
        ok_btn.setFixedHeight(40)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def get_chunk_data(self):
        return (self.start_spin.value(), self.end_spin.value(), self.text_edit.toPlainText().strip())


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
        self._items: List[ChunkItem] = []          # one entry per displayed chunk
        self._deleted_chunk_timestamps = set()     # timestamps removed by the user
        self._edited_flags: List[bool] = []         # set by get_edited_chunks()
        self._video_filename = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 12, 0, 0)

        desc = QLabel("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet(f"color: {theme.TEXT}; background-color: transparent;")
        layout.addWidget(desc)

        self.status_label = QLabel("Waiting for transcription...")
        self.status_label.setStyleSheet(f"color: {theme.TEXT}; background-color: transparent; padding: 0px 12px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(250)
        chunks_widget = QWidget()
        chunks_widget.setStyleSheet(f"QWidget {{ background-color: {theme.PANEL}; }}")
        self.chunks_layout = QVBoxLayout()
        self.chunks_layout.setSpacing(12)
        chunks_widget.setLayout(self.chunks_layout)
        scroll.setWidget(chunks_widget)
        layout.addWidget(scroll, stretch=1)

        layout.addSpacing(8)

        self.save_transcript_btn = QPushButton("Save Transcript")
        self.save_transcript_btn.setEnabled(False)
        self.save_transcript_btn.setFixedHeight(56)
        self.save_transcript_btn.setMaximumWidth(200)
        self.save_transcript_btn.clicked.connect(self._on_save_transcript_clicked)

        self.generate_btn = QPushButton("Generate Comp")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setFixedHeight(56)
        self.generate_btn.setMaximumWidth(200)
        self.generate_btn.clicked.connect(self._on_generate_clicked)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_transcript_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addSpacing(20)
        btn_layout.addWidget(self.generate_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        btn_layout.addStretch()
        layout.addLayout(btn_layout, stretch=0)

        layout.addStretch()

        # Create result_label for code reference, but don't add to layout to save space
        self.result_label = QLabel("")
        self.result_label.setStyleSheet(f"background-color: transparent; color: {theme.GREEN}; font-weight: bold;")

        self.setLayout(layout)

    def set_status(self, text):
        self.status_label.setText(text)

    def _clear_cards(self):
        """Remove every card widget from the scroll layout."""
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def populate_chunks(self, chunks, video_filename=None):
        self._clear_cards()
        self._items = []
        self._video_filename = video_filename

        typing_targets = []
        for timestamp, text in chunks:
            card, text_edit = self._create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)
            typing_targets.append((text_edit, text))
            self._items.append(ChunkItem(
                timestamp=timestamp,
                original_text=text,
                text_edit=text_edit,
                card=card,
                is_manual=False,
            ))

        self.chunks_layout.addStretch()
        self.generate_btn.setEnabled(True)
        self.save_transcript_btn.setEnabled(True)
        self._typing_animator.animate_sequence(typing_targets)

    def restart_typing(self):
        self._typing_animator.restart()

    def fill_all_chunks(self):
        """If the typing animation is still running, finish it instantly.

        No-op once typing has completed, so a click to edit (or after editing)
        never overwrites the user's text.
        """
        if not self._typing_animator.is_active():
            return
        self._typing_animator.stop()
        for item in self._items:
            item.text_edit.setPlainText(item.original_text)

    def _create_chunk_card(self, timestamp, text):
        card = ChunkCard()
        card.chunk_timestamp = timestamp
        card.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid {theme.GREEN};
                border-radius: 6px;
                margin: 0px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet(f"color: {theme.GREEN}; font-weight: 600; font-size: 11px; background-color: transparent;")
        header_layout.addWidget(timestamp_label)
        header_layout.addStretch()

        # X icon SVG - clean and symmetrical, with hover variant
        x_svg = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="{theme.GREEN}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''
        x_svg_hover = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18M6 6L18 18" stroke="{theme.GREEN_HOVER}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''
        x_icon = icon_from_svg(x_svg)
        x_icon_hover = icon_from_svg(x_svg_hover)

        delete_btn = QPushButton()
        delete_btn.setIcon(x_icon)
        delete_btn.setIconSize(QSize(18, 18))
        delete_btn.setMaximumWidth(24)
        delete_btn.setMaximumHeight(24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)

        # Store icons for hover effect
        delete_btn._normal_icon = x_icon
        delete_btn._hover_icon = x_icon_hover

        def on_hover_enter():
            delete_btn.setIcon(delete_btn._hover_icon)

        def on_hover_leave():
            delete_btn.setIcon(delete_btn._normal_icon)

        delete_btn.enterEvent = lambda e: on_hover_enter()
        delete_btn.leaveEvent = lambda e: on_hover_leave()
        delete_btn.clicked.connect(lambda: self._delete_chunk(timestamp))
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

        text_edit = QTextEdit()
        text_edit.setMinimumHeight(60)
        text_edit.setMaximumHeight(100)
        text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {theme.BG};
                color: {theme.TEXT};
                border: 1px solid {theme.green_rgba(0.3)};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QTextEdit:focus {{
                background-color: {theme.BG_FOCUS};
                border: 2px solid {theme.GREEN_BRIGHT};
            }}
        """)
        layout.addWidget(text_edit)

        card.setLayout(layout)
        return card, text_edit

    def _delete_chunk(self, timestamp):
        """Delete a chunk: drop its ChunkItem and remove its card from the layout."""
        self._deleted_chunk_timestamps.add(timestamp)

        for item in self._items:
            if item.timestamp == timestamp:
                self.chunks_layout.removeWidget(item.card)
                item.card.deleteLater()
                break

        self._items = [it for it in self._items if it.timestamp != timestamp]

    def get_edited_chunks(self):
        """Get the current chunk texts and record which were actually edited."""
        edited = []
        edited_flags = []
        debug_logger.debug(f"Detecting edits in {len(self._items)} chunks")

        for idx, item in enumerate(self._items):
            current_text = item.text_edit.toPlainText()
            if not current_text:
                current_text = item.original_text

            # Manual chunks are always treated as edited
            was_edited = item.is_manual or (current_text != item.original_text)

            if was_edited:
                marker = "[MANUAL]" if item.is_manual else "[EDITED]"
                debug_logger.debug(f"  Chunk {idx} {marker}: ts={item.timestamp}, "
                                   f"original={item.original_text[:40]}..., current={current_text[:40]}...")
            else:
                debug_logger.debug(f"  Chunk {idx} [UNEDITED]")

            edited.append((item.timestamp, current_text))
            edited_flags.append(was_edited)

        debug_logger.debug(f"Edit detection complete: {sum(edited_flags)}/{len(edited_flags)} chunks were edited")
        self._edited_flags = edited_flags
        return edited

    def get_edited_flags(self):
        """Get which chunks were actually edited (populated by get_edited_chunks)."""
        return self._edited_flags

    def get_manually_added_chunks(self):
        """Get manually added chunks as List[List[List[Word]]]."""
        return [item.words for item in self._items if item.is_manual]

    def get_deleted_chunk_timestamps(self):
        """Get set of timestamps for chunks that were deleted."""
        return self._deleted_chunk_timestamps

    def get_manual_chunk_timestamps(self):
        """Get start times (float) of manually added chunks, for identification."""
        timestamps = []
        for item in self._items:
            if item.is_manual and item.words and item.words[0]:
                timestamps.append(item.words[0][0].start)
        return timestamps

    def open_add_chunk_dialog(self, start_time=None, end_time=None):
        """Open add chunk dialog with optional pre-filled times."""
        dialog = AddChunkDialog(self, start_time=start_time, end_time=end_time)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            start_time, end_time, text = dialog.get_chunk_data()

            if not text:
                QMessageBox.warning(self, "Error", "Chunk text cannot be empty")
                return

            if start_time >= end_time:
                QMessageBox.warning(self, "Error", "Start time must be before end time")
                return

            self._create_and_add_chunk(start_time, end_time, text)

    def _create_and_add_chunk(self, start_time, end_time, text):
        """Create a manual chunk (with proportional word timing) and insert it in order."""
        # Build Word objects from text with proportional timing
        words_text = text.split()
        duration = end_time - start_time
        word_duration = duration / len(words_text) if words_text else 0

        chunk_lines = [[]]
        current_line_chars = 0
        max_chars_per_line = 20

        for i, word_text in enumerate(words_text):
            word_len = len(word_text)
            space_len = 1 if chunk_lines[-1] else 0

            # Break line if exceeds character limit
            if chunk_lines[-1] and current_line_chars + space_len + word_len > max_chars_per_line:
                chunk_lines.append([])
                current_line_chars = 0

            word_start = start_time + (i * word_duration)
            word_end = start_time + ((i + 1) * word_duration)
            word = Word(text=word_text, start=word_start, end=word_end)
            chunk_lines[-1].append(word)
            current_line_chars += space_len + word_len

        debug_logger.debug(f"Added manual chunk: {start_time:.3f}s - {end_time:.3f}s, {len(words_text)} words")

        # Reconstruct display text from all lines
        display_text = "\n".join(" ".join(w.text for w in line) for line in chunk_lines)

        timestamp_str = f"{start_time:.3f}"
        card, text_edit = self._create_chunk_card(timestamp_str, display_text)
        text_edit.setPlainText(display_text)

        # Find correct sorted position by start time
        insert_pos = 0
        new_time = float(timestamp_str)
        for i, item in enumerate(self._items):
            if float(item.timestamp) < new_time:
                insert_pos = i + 1

        self._items.insert(insert_pos, ChunkItem(
            timestamp=timestamp_str,
            original_text=display_text,
            text_edit=text_edit,
            card=card,
            is_manual=True,
            words=chunk_lines,
        ))
        self.chunks_layout.insertWidget(insert_pos, card)
        debug_logger.debug(f"Inserted manual chunk at position {insert_pos}")

    def _on_save_transcript_clicked(self):
        """Save edited chunks as SRT file."""
        if not self._items:
            self.result_label.setText("Error: No chunks available")
            return

        default_name = "subtitles.srt"
        if self._video_filename:
            default_name = Path(self._video_filename).stem + ".srt"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Subtitle File",
            default_name,
            "SRT Files (*.srt);;All Files (*)"
        )

        if not file_path:
            return

        try:
            def format_timestamp(seconds):
                hours = int(seconds) // 3600
                minutes = (int(seconds) % 3600) // 60
                secs = int(seconds) % 60
                millis = int((seconds % 1) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

            srt_entries = []
            for idx, item in enumerate(self._items, 1):
                text = item.text_edit.toPlainText().strip()
                if text:
                    start_sec = float(item.timestamp)
                    # End time is start of next chunk, or start + 2s for last chunk
                    if idx < len(self._items):
                        end_sec = float(self._items[idx].timestamp)
                    else:
                        end_sec = start_sec + 2.0

                    srt_entries.append(f"{idx}\n{format_timestamp(start_sec)} --> {format_timestamp(end_sec)}\n{text}\n")

            Path(file_path).write_text("\n".join(srt_entries), encoding='utf-8')
            self.result_label.setText(f"✓ Saved: {Path(file_path).name}")
            debug_logger.info(f"Transcript saved to: {file_path}")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")
            debug_logger.error(f"Failed to save transcript: {str(e)}")

    def _on_generate_clicked(self):
        self.generate_btn.setEnabled(False)
        self.generation_started.emit()
