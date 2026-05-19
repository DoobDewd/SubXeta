import logging
from difflib import SequenceMatcher
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGraphicsOpacityEffect, QFileDialog
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

from ui.styles import get_stylesheet
from ui.tab_bar import TabBar
from ui.steps.step1_transcribe import Step1Widget
from ui.steps.step2_review import Step2Widget
from core.transcription import TranscriptionWorker
from core.chunks import load_whisper_json, group_into_chunks, chunk_to_texts
from core.models import Word
from core.subtitle_gen import generate_single_comp
from pathlib import Path

logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Comp App")
        self.setGeometry(100, 100, 1200, 800)
        self.setFixedSize(1200, 800)

        self._transcription_worker = None
        self._current_json_path = None
        self._original_chunks = None

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)

        nav_container = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(40, 12, 40, 0)
        nav_layout.setSpacing(0)
        self.tab_bar = TabBar()
        self.tab_bar.tab_changed.connect(self._show_step)
        nav_layout.addWidget(self.tab_bar)
        nav_container.setLayout(nav_layout)
        nav_container.setStyleSheet("background-color: #1a1a1a;")
        main_layout.addWidget(nav_container)

        main_layout.addWidget(self._create_content_area(), 1)

        self.setStyleSheet(get_stylesheet())

    def _create_content_area(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)

        self.step1 = Step1Widget()
        self.step1_effect = QGraphicsOpacityEffect()
        self.step1_effect.setOpacity(1.0)
        self.step1.setGraphicsEffect(self.step1_effect)
        self.step1.transcription_started.connect(self._on_transcription_started)
        layout.addWidget(self.step1)

        self.step2 = Step2Widget()
        self.step2_effect = QGraphicsOpacityEffect()
        self.step2_effect.setOpacity(0.0)
        self.step2.setGraphicsEffect(self.step2_effect)
        self.step2.setVisible(False)
        self.step2.generation_started.connect(self._on_generation_started)
        layout.addWidget(self.step2)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        return scroll

    def _on_transcription_started(self, file_path):
        """Start transcription worker when button is clicked."""
        self.step1.transcribe_btn.setEnabled(False)
        self.step1.progress_bar.setValue(0)

        self._transcription_worker = TranscriptionWorker(file_path, model="large")
        self._transcription_worker.progress.connect(self.step1.progress_bar.setValue)
        self._transcription_worker.finished.connect(self._on_transcription_finished)
        self._transcription_worker.error.connect(self._on_transcription_error)
        self._transcription_worker.start()

    def _on_transcription_finished(self, json_path):
        """Handle successful transcription."""
        self._current_json_path = json_path
        self.step1.stop_shimmer()
        self.step1.progress_bar.setVisible(False)

        try:
            words = load_whisper_json(json_path)
            chunks = group_into_chunks(words, max_chars_per_line=20, pause_threshold=0.3)
            self._original_chunks = chunks

            chunk_data = []
            for chunk in chunks:
                all_words = []
                for line in chunk:
                    all_words.extend(line)
                timestamp = f"{all_words[0].start:.3f}"
                # Use chunk_to_texts to get proper multi-line format
                text_variant = chunk_to_texts(chunk, pause_threshold=0.3)
                # Replace literal \n with actual newlines for display
                text = text_variant.english.replace("\\n", "\n")
                chunk_data.append((timestamp, text))

            self.step2.set_status("Review and edit chunks as needed, then click Generate Comp")
            self.step2.populate_chunks(chunk_data)
            self.tab_bar.enable_step(2, on_complete=lambda: self._show_step(2))

        except Exception as e:
            self._on_transcription_error(f"Failed to process transcription: {str(e)}")

    def _on_transcription_error(self, error_msg):
        """Handle transcription error."""
        self.step1.stop_shimmer()
        self.step1.transcribe_btn.setEnabled(True)
        self.step1.progress_bar.setVisible(False)

    def _map_edited_words_to_original(self, original_words, edited_words):
        """Map edited words to original words using sequence matching, handling multiple edits."""
        debug_logger.debug(f"Word mapping: original={original_words} → edited={edited_words}")

        if not original_words:
            debug_logger.debug(f"No original words, mapping all {len(edited_words)} edited words to None")
            return {i: None for i in range(len(edited_words))}

        # Use SequenceMatcher to find matching blocks
        matcher = SequenceMatcher(None, original_words, edited_words)
        matching_blocks = matcher.get_matching_blocks()
        debug_logger.debug(f"SequenceMatcher blocks: {matching_blocks}")

        # Build a mapping of edited word index to original word index
        mapping = {}
        used_original_indices = set()

        for block in matching_blocks[:-1]:  # Skip the final end marker
            orig_start, edit_start, size = block
            debug_logger.debug(f"  Matching block: orig[{orig_start}:{orig_start+size}] ↔ edit[{edit_start}:{edit_start+size}]")
            # Map matched words
            for i in range(size):
                mapping[edit_start + i] = orig_start + i
                used_original_indices.add(orig_start + i)

        # Find unmatched original indices and edited positions
        unmatched_orig_indices = [i for i in range(len(original_words)) if i not in used_original_indices]
        unmatched_edit_indices = [i for i in range(len(edited_words)) if i not in mapping]

        debug_logger.debug(f"  Unmatched original indices: {unmatched_orig_indices}")
        debug_logger.debug(f"  Unmatched edited indices: {unmatched_edit_indices}")

        # Map unmatched edited words to unmatched original words in position order
        for edit_idx, orig_idx in zip(unmatched_edit_indices, unmatched_orig_indices):
            mapping[edit_idx] = orig_idx
            debug_logger.debug(f"    Mapping unmatched edit[{edit_idx}] → orig[{orig_idx}]")

        # If there are more unmatched edited words than original, map remaining to last unmatched original
        if len(unmatched_edit_indices) > len(unmatched_orig_indices):
            fallback_orig = unmatched_orig_indices[-1] if unmatched_orig_indices else len(original_words) - 1
            extra_edits = unmatched_edit_indices[len(unmatched_orig_indices):]
            for edit_idx in extra_edits:
                mapping[edit_idx] = fallback_orig
                debug_logger.debug(f"    Mapping extra edit[{edit_idx}] → orig[{fallback_orig}] (fallback)")

        debug_logger.debug(f"Final word mapping: {mapping}")
        return mapping

    def _on_generation_started(self):
        """Generate comp from edited chunks."""
        try:
            if not self._current_json_path:
                self.step2.result_label.setText("Error: No transcription data")
                return

            # Load original words
            words = load_whisper_json(self._current_json_path)

            # Get edited chunk texts and which chunks were actually edited
            edited_chunks = self.step2.get_edited_chunks()
            edited_flags = self.step2.get_edited_flags()

            # Rebuild chunks with edited text but original timing
            rebuilt_chunks = []
            debug_logger.debug(f"Starting chunk reconstruction from {len(edited_chunks)} chunks")

            # Edge case: check for empty edits
            empty_chunks = [i for i, (_, text) in enumerate(edited_chunks) if not text.strip()]
            if empty_chunks:
                debug_logger.debug(f"WARN: {len(empty_chunks)} empty chunks: {empty_chunks}")

            for chunk_idx, (timestamp_str, edited_text) in enumerate(edited_chunks):
                # If chunk wasn't edited, use the original chunk structure as-is
                if chunk_idx < len(edited_flags) and not edited_flags[chunk_idx]:
                    debug_logger.debug(f"Chunk {chunk_idx}: UNEDITED, using original structure")
                    if chunk_idx < len(self._original_chunks):
                        rebuilt_chunks.append(self._original_chunks[chunk_idx])
                    continue

                debug_logger.debug(f"Chunk {chunk_idx}: EDITED, reconstructing with new text")

                # Chunk was edited, so reconstruct it with new text and timing
                if chunk_idx < len(self._original_chunks):
                    original_chunk = self._original_chunks[chunk_idx]
                else:
                    original_chunk = []
                    debug_logger.debug(f"  No original chunk at index {chunk_idx}, starting from scratch")

                chunk_lines = []
                # Split by newlines to preserve line structure
                text_lines = edited_text.split('\n')
                debug_logger.debug(f"  Edited text has {len(text_lines)} line(s)")

                for line_idx, text_line in enumerate(text_lines):
                    edited_words = text_line.split()
                    debug_logger.debug(f"  Line {line_idx}: {len(edited_words)} edited words: {edited_words}")

                    # Get original words for this specific line
                    if line_idx < len(original_chunk):
                        original_words_list = original_chunk[line_idx]
                    else:
                        original_words_list = []

                    # Map edited words to original words using sequence matching
                    original_texts = [w.text for w in original_words_list] if original_words_list else []
                    debug_logger.debug(f"    Original line {line_idx}: {original_texts}")
                    word_mapping = self._map_edited_words_to_original(original_texts, edited_words)

                    line_words = []
                    current_line_chars = 0

                    # Track which original words have been used for split timing
                    split_words = {}

                    # Map edited text back to original words
                    for edit_idx, word_text in enumerate(edited_words):
                        word_len = len(word_text)
                        space_len = 1 if line_words else 0

                        # Break line if exceeds 20 chars
                        if line_words and current_line_chars + space_len + word_len > 20:
                            debug_logger.debug(f"      Line break at word {edit_idx} (total chars would be {current_line_chars + space_len + word_len})")
                            chunk_lines.append(line_words)
                            line_words = []
                            current_line_chars = 0

                        # Get the original word this edited word maps to
                        orig_idx = word_mapping.get(edit_idx)
                        debug_logger.debug(f"      Word {edit_idx}: '{word_text}' maps to original[{orig_idx}]")

                        if orig_idx is not None and orig_idx < len(original_words_list):
                            original_word = original_words_list[orig_idx]

                            # Check if this original word needs to be split among multiple edited words
                            matching_edited_indices = [i for i, o in word_mapping.items() if o == orig_idx]

                            if len(matching_edited_indices) > 1:
                                # This original word is being split among multiple edited words
                                if orig_idx not in split_words:
                                    # First time encountering this split: calculate split timing
                                    duration = original_word.end - original_word.start
                                    num_parts = len(matching_edited_indices)
                                    split_duration = duration / num_parts
                                    split_words[orig_idx] = split_duration
                                    debug_logger.debug(f"        SPLIT: Original[{orig_idx}] (duration={duration:.3f}s) split into {num_parts} parts ({split_duration:.3f}s each)")

                                position = matching_edited_indices.index(edit_idx)
                                start_time = original_word.start + (split_words[orig_idx] * position)
                                end_time = original_word.start + (split_words[orig_idx] * (position + 1))
                                debug_logger.debug(f"        Part {position+1}/{len(matching_edited_indices)}: {start_time:.3f}s → {end_time:.3f}s")
                                edited_word = Word(
                                    text=word_text,
                                    start=start_time,
                                    end=end_time
                                )
                            else:
                                # This edited word maps directly to one original word
                                debug_logger.debug(f"        Direct map: {original_word.start:.3f}s → {original_word.end:.3f}s")
                                edited_word = Word(
                                    text=word_text,
                                    start=original_word.start,
                                    end=original_word.end
                                )
                        else:
                            debug_logger.debug(f"      Skipping word {edit_idx}: no mapping found")
                            continue

                        line_words.append(edited_word)
                        current_line_chars += space_len + word_len

                    if line_words:
                        chunk_lines.append(line_words)

                if chunk_lines:
                    rebuilt_chunks.append(chunk_lines)

            # Generate comp
            debug_logger.debug(f"Generating comp from {len(rebuilt_chunks)} chunks")
            comp_content = generate_single_comp(rebuilt_chunks, fps=24, pause_threshold=0.3)
            debug_logger.debug(f"Comp generated: {len(comp_content)} bytes")

            # Save comp file with "Save As" dialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Composition",
                "subtitle.comp",
                "Fusion Compositions (*.comp);;All Files (*)"
            )

            if file_path:
                output_path = Path(file_path)
                debug_logger.debug(f"Writing comp to: {output_path}")
                output_path.write_text(comp_content)
                file_size = output_path.stat().st_size
                debug_logger.debug(f"Comp file written: {file_size} bytes")
                self.step2.progress_bar.setVisible(False)
                self.step2.generate_btn.setEnabled(True)
                self.step2.result_label.setText(f"✓ Generated: {output_path.name}")
            else:
                debug_logger.debug("User cancelled comp save")
                self.step2.progress_bar.setVisible(False)
                self.step2.generate_btn.setEnabled(True)
                self.step2.result_label.setText("Cancelled")

            # Delete temp JSON file after comp generation is complete
            try:
                Path(self._current_json_path).unlink()
                logger.info("Cleaned up temporary JSON file")
            except Exception as e:
                logger.warning(f"Could not delete temp JSON: {e}")

        except Exception as e:
            self.step2.progress_bar.setVisible(False)
            self.step2.generate_btn.setEnabled(True)
            self.step2.result_label.setText(f"Error: {str(e)}")

    def _show_step(self, step):
        self.tab_bar.set_active(step, animate=True)

        outgoing = self.step1 if step == 2 else self.step2
        incoming = self.step2 if step == 2 else self.step1
        out_effect = self.step1_effect if step == 2 else self.step2_effect
        in_effect = self.step2_effect if step == 2 else self.step1_effect

        if not outgoing.isVisible():
            incoming.setVisible(True)
            in_effect.setOpacity(1.0)
            if step == 2:
                self.step2.restart_typing()
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
                self.step2.restart_typing()

        fade_out.finished.connect(on_fade_out_done)
        self._fade_out_anim = fade_out
        fade_out.start()
