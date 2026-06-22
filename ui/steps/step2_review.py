import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QLabel, QPushButton, QProgressBar,
    QScrollArea, QWidget, QTextEdit, QHBoxLayout, QFileDialog,
    QDialog, QDoubleSpinBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QPainter, QFont
from ui.animations import CRTAnimatedMixin, TypingAnimator
from core.models import Word

debug_logger = logging.getLogger(f"{__name__}.debug")


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
        start_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(start_label)
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setMinimum(0.0)
        self.start_spin.setMaximum(9999.99)
        self.start_spin.setDecimals(2)
        self.start_spin.setValue(self._prefilled_start if self._prefilled_start is not None else 0.0)
        layout.addWidget(self.start_spin)

        end_label = QLabel("End Time (seconds):")
        end_label.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(end_label)
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setMinimum(0.0)
        self.end_spin.setMaximum(9999.99)
        self.end_spin.setDecimals(2)
        self.end_spin.setValue(self._prefilled_end if self._prefilled_end is not None else 1.0)
        layout.addWidget(self.end_spin)

        text_label = QLabel("Text:")
        text_label.setStyleSheet("color: #e0e0e0;")
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
        self._chunks = []
        self._original_texts = []
        self._full_chunk_texts = []
        self._video_filename = None
        self._transcribed_original_texts = []  # Original transcribed chunks (never modified)
        self._manually_added_chunks = []
        self._deleted_chunk_timestamps = set()  # Track deleted chunks
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)

        desc = QLabel("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        desc_font = QFont()
        desc_font.setPointSize(12)
        desc.setFont(desc_font)
        desc.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(desc)

        self.status_label = QLabel("Waiting for transcription...")
        self.status_label.setStyleSheet("color: #e0e0e0; background-color: transparent; padding: 0px 12px;")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(250)
        chunks_widget = QWidget()
        chunks_widget.setStyleSheet("QWidget { background-color: #191e1c; }")
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
        self.result_label.setStyleSheet("background-color: transparent; color: #00ff88; font-weight: bold;")

        self.setLayout(layout)

    def set_status(self, text):
        self.status_label.setText(text)

    def populate_chunks(self, chunks, video_filename=None):
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._chunks = []
        self._original_texts = []
        self._full_chunk_texts = []
        self._transcribed_original_texts = []  # Save the original transcribed chunks
        self._manually_added_chunks = []
        self._video_filename = video_filename
        typing_targets = []
        for timestamp, text in chunks:
            card, text_edit = self._create_chunk_card(timestamp, text)
            self.chunks_layout.addWidget(card)
            typing_targets.append((text_edit, text))
            self._chunks.append((timestamp, text_edit))
            self._original_texts.append((timestamp, text))
            self._transcribed_original_texts.append((timestamp, text))  # Store immutable copy
            self._full_chunk_texts.append(text)

        self.chunks_layout.addStretch()
        self.generate_btn.setEnabled(True)
        self.save_transcript_btn.setEnabled(True)
        self._typing_animator.animate_sequence(typing_targets)

    def restart_typing(self):
        self._typing_animator.restart()

    def stop_animation_and_populate(self):
        """Stop typing animation and show all current text (including edits)."""
        self._typing_animator.stop()
        # For chunks still animating, populate them with their current text (which includes any edits)
        for i, (timestamp, text_edit) in enumerate(self._chunks):
            current_text = text_edit.toPlainText()
            # If text is empty or still animating, set it to show full content
            if not current_text or len(current_text) < 1:
                if i < len(self._full_chunk_texts):
                    text_edit.setPlainText(self._full_chunk_texts[i])
            # Otherwise keep the current edited text as-is

    def _create_chunk_card(self, timestamp, text):
        card = ChunkCard()
        card.chunk_timestamp = timestamp
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

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        header_layout.setContentsMargins(0, 0, 0, 0)

        timestamp_label = QLabel(timestamp)
        timestamp_label.setStyleSheet("color: #00ff88; font-weight: 600; font-size: 11px; background-color: transparent;")
        header_layout.addWidget(timestamp_label)
        header_layout.addStretch()

        delete_btn = QPushButton("✕")
        delete_btn.setMaximumWidth(24)
        delete_btn.setMaximumHeight(24)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ff4444;
                border: 1px solid #ff4444;
                border-radius: 3px;
                font-weight: bold;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 0.2);
            }
        """)
        delete_btn.clicked.connect(lambda: self._delete_chunk(timestamp))
        header_layout.addWidget(delete_btn)

        layout.addLayout(header_layout)

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

    def _delete_chunk(self, timestamp):
        """Delete a chunk by removing from display and internal lists."""
        # Track as deleted
        self._deleted_chunk_timestamps.add(timestamp)

        # Find and remove from all tracking lists by timestamp
        self._chunks = [(ts, edit) for ts, edit in self._chunks if ts != timestamp]
        self._original_texts = [(ts, text) for ts, text in self._original_texts if ts != timestamp]
        self._transcribed_original_texts = [(ts, text) for ts, text in self._transcribed_original_texts if ts != timestamp]

        # Rebuild _full_chunk_texts to match filtered _original_texts
        self._full_chunk_texts = [text for ts, text in self._original_texts]

        # Remove from layout widget
        for i in range(self.chunks_layout.count()):
            widget = self.chunks_layout.itemAt(i).widget()
            if widget and hasattr(widget, 'chunk_timestamp') and widget.chunk_timestamp == timestamp:
                self.chunks_layout.removeWidget(widget)
                widget.deleteLater()
                break

    def get_edited_chunks(self):
        """Get the currently edited chunks and track which were actually edited."""
        edited = []
        edited_flags = []

        # Get timestamps of manual chunks for identification
        manual_timestamps = self.get_manual_chunk_timestamps()
        debug_logger.debug(f"Detecting edits in {len(self._chunks)} chunks (manual timestamps: {manual_timestamps})")

        for idx, (timestamp, text_edit) in enumerate(self._chunks):
            current_text = text_edit.toPlainText()
            # Use index-based lookup like the old code - arrays stay aligned
            original_text = self._full_chunk_texts[idx] if idx < len(self._full_chunk_texts) else ""

            if not current_text:
                current_text = original_text

            # Check if this chunk is manually added by matching timestamp
            ts_float = float(timestamp)
            is_manually_added = any(abs(ts_float - mt) < 0.001 for mt in manual_timestamps)

            # Manual chunks are always marked as edited
            was_edited = is_manually_added or (current_text != original_text)

            if was_edited:
                marker = "[MANUAL]" if is_manually_added else "[EDITED]"
                debug_logger.debug(f"  Chunk {idx} {marker}:")
                debug_logger.debug(f"    Timestamp: {timestamp}, Original: {original_text[:40]}..., Current: {current_text[:40]}...")
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

    def get_manually_added_chunks(self):
        """Get manually added chunks as List[List[List[Word]]]."""
        return self._manually_added_chunks

    def get_deleted_chunk_timestamps(self):
        """Get set of timestamps for chunks that were deleted."""
        return self._deleted_chunk_timestamps

    def get_manual_chunk_timestamps(self):
        """Get timestamps of manually added chunks for identification."""
        timestamps = []
        for chunk in self._manually_added_chunks:
            if chunk and chunk[0]:
                timestamps.append(chunk[0][0].start)
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
        """Create and add a chunk to the display."""
        # Create Word objects from text with proportional timing
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

        self._manually_added_chunks.append(chunk_lines)
        debug_logger.debug(f"Added manual chunk: {start_time:.3f}s - {end_time:.3f}s, {len(words_text)} words")

        # Create the new chunk widget
        text_lines = []
        for line in chunk_lines:
            line_text = " ".join([w.text for w in line])
            text_lines.append(line_text)
        text = "\n".join(text_lines)

        timestamp_str = f"{start_time:.3f}"
        card, text_edit = self._create_chunk_card(timestamp_str, text)
        text_edit.setPlainText(text)

        # Find correct sorted position
        insert_pos = 0
        new_time = float(timestamp_str)
        for i, (ts, _) in enumerate(self._chunks):
            if float(ts) < new_time:
                insert_pos = i + 1

        # Before inserting, capture current state for debugging
        debug_logger.debug(f"Before insert: {len(self._chunks)} chunks, inserting at pos {insert_pos}")
        if insert_pos > 0:
            prev_ts, prev_edit = self._chunks[insert_pos - 1]
            debug_logger.debug(f"  Chunk before insert pos: ts={prev_ts}, text={prev_edit.toPlainText()[:40]}")

        # Insert into ALL data structures at the same position
        self._chunks.insert(insert_pos, (timestamp_str, text_edit))
        self._original_texts.insert(insert_pos, (timestamp_str, text))
        self._full_chunk_texts.insert(insert_pos, text)

        # After insert, check if previous chunk is still intact
        if insert_pos > 0:
            check_ts, check_edit = self._chunks[insert_pos - 1]
            debug_logger.debug(f"After insert: chunk before still has text={check_edit.toPlainText()[:40]}")

        # Insert into layout at the same position
        self.chunks_layout.insertWidget(insert_pos, card)
        debug_logger.debug(f"Inserted chunk at position {insert_pos}")

    def _refresh_chunk_display(self):
        """Rebuild the chunk display with both original and manually added chunks."""
        # Stop typing animator to avoid crash when rebuilding display
        self._typing_animator.stop()

        # Clear existing display
        while self.chunks_layout.count():
            item = self.chunks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._chunks = []
        self._original_texts = []
        self._full_chunk_texts = []

        # Collect all chunks (original + manual) with their start times
        all_chunks_with_time = []

        # Add original transcribed chunks
        for i, (timestamp, original_text) in enumerate(self._transcribed_original_texts):
            all_chunks_with_time.append(('original', i, float(timestamp), timestamp, original_text))

        # Add manually added chunks
        for i, chunk_words_list in enumerate(self._manually_added_chunks):
            if chunk_words_list and chunk_words_list[0]:
                start_time = chunk_words_list[0][0].start
                # Reconstruct text from ALL lines (not just first line)
                text_lines = []
                for line in chunk_words_list:
                    line_text = " ".join([w.text for w in line])
                    text_lines.append(line_text)
                text = "\n".join(text_lines)
                all_chunks_with_time.append(('manual', i, start_time, f"{start_time:.3f}", text))

        # Sort by start time
        all_chunks_with_time.sort(key=lambda x: x[2])

        # Display in order (no animation, just show text)
        for chunk_type, idx, _, timestamp_str, text in all_chunks_with_time:
            card, text_edit = self._create_chunk_card(timestamp_str, text)
            text_edit.setPlainText(text)
            self.chunks_layout.addWidget(card)
            self._chunks.append((timestamp_str, text_edit))
            self._original_texts.append((timestamp_str, text))
            self._full_chunk_texts.append(text)

        self.chunks_layout.addStretch()

    def _on_save_transcript_clicked(self):
        """Save edited chunks as SRT file."""
        if not self._chunks:
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
            for idx, (timestamp_str, text_edit) in enumerate(self._chunks, 1):
                text = text_edit.toPlainText().strip()
                if text:
                    start_sec = float(timestamp_str)
                    # End time is start of next chunk, or start + 2s for last chunk
                    if idx < len(self._chunks):
                        next_timestamp = float(self._chunks[idx][0])
                        end_sec = next_timestamp
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

