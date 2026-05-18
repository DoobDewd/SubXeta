from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGraphicsOpacityEffect
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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Comp App")
        self.setGeometry(100, 100, 1200, 800)
        self.setFixedSize(1200, 800)

        self._transcription_worker = None
        self._current_json_path = None

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
            chunks = group_into_chunks(words, max_chars_per_line=30, pause_threshold=0.3)

            chunk_data = []
            for chunk in chunks:
                all_words = []
                for line in chunk:
                    all_words.extend(line)
                timestamp = f"{all_words[0].start:.3f}"
                text = " ".join(w.text for w in all_words)
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

    def _on_generation_started(self):
        """Generate comp from edited chunks."""
        try:
            if not self._current_json_path:
                self.step2.result_label.setText("Error: No transcription data")
                return

            # Load original words
            words = load_whisper_json(self._current_json_path)

            # Get edited chunk texts
            edited_chunks = self.step2.get_edited_chunks()

            # Rebuild chunks with edited text but original timing
            rebuilt_chunks = []
            word_idx = 0

            for timestamp_str, edited_text in edited_chunks:
                chunk_lines = []
                edited_words = edited_text.split()

                # Map edited text back to original words
                line_words = []
                for word_text in edited_words:
                    if word_idx < len(words):
                        original_word = words[word_idx]
                        # Create a new Word with edited text but original timing
                        edited_word = Word(
                            text=word_text,
                            start=original_word.start,
                            end=original_word.end
                        )
                        line_words.append(edited_word)
                        word_idx += 1

                if line_words:
                    chunk_lines.append(line_words)

                if chunk_lines:
                    rebuilt_chunks.append(chunk_lines)

            # Generate comp
            comp_content = generate_single_comp(rebuilt_chunks, fps=24, pause_threshold=0.3)

            # Save comp file
            output_path = Path("subs") / "subtitles.comp"
            output_path.parent.mkdir(exist_ok=True, parents=True)
            output_path.write_text(comp_content)

            self.step2.progress_bar.setVisible(False)
            self.step2.generate_btn.setEnabled(True)
            self.step2.result_label.setText(f"✓ Generated: {output_path}")

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
