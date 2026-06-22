import logging
from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGraphicsOpacityEffect, QFileDialog, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt, QEvent

from ui.styles import get_stylesheet
from ui.tab_bar import TabBar
from ui.settings_widget import SettingsWidget
from ui.steps.step1_transcribe import Step1Widget
from ui.steps.step2_review import Step2Widget
from ui.audio_player import AudioPlayerWidget
from core.transcription import TranscriptionWorker
from core.chunks import load_whisper_json, group_into_chunks, chunk_to_texts, rebuild_chunks_with_edits
from core.subtitle_gen_alien import generate_single_comp
from core.settings import load_settings, save_settings
from pathlib import Path

logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SubXeta")
        self.setGeometry(100, 100, 1200, 1000)
        self.setFixedSize(1200, 1000)

        # Load window icon
        icon_path = Path(__file__).parent.parent / 'icon.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._transcription_worker = None
        self._current_json_path = None
        self._original_chunks = None
        self._current_video_path = None
        self._settings = load_settings()
        self._step2_typing_played = False

        # Install event filter for global keyboard shortcuts on the application
        QApplication.instance().installEventFilter(self)

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

        # Connect audio player to step2 after both are created
        self.audio.add_chunk_requested.connect(self.step2.open_add_chunk_dialog)

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

        self.audio = AudioPlayerWidget()
        self.audio_effect = QGraphicsOpacityEffect()
        self.audio_effect.setOpacity(0.0)
        self.audio.setGraphicsEffect(self.audio_effect)
        self.audio.setVisible(False)
        layout.addWidget(self.audio)

        self.step2 = Step2Widget()
        self.step2_effect = QGraphicsOpacityEffect()
        self.step2_effect.setOpacity(0.0)
        self.step2.setGraphicsEffect(self.step2_effect)
        self.step2.setVisible(False)
        self.step2.generation_started.connect(self._on_generation_started)
        layout.addWidget(self.step2)

        self.settings = SettingsWidget()
        self.settings_effect = QGraphicsOpacityEffect()
        self.settings_effect.setOpacity(0.0)
        self.settings.setGraphicsEffect(self.settings_effect)
        self.settings.setVisible(False)
        self.settings.settings_changed.connect(self._on_settings_changed)
        layout.addWidget(self.settings)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        return scroll

    def _on_transcription_started(self, file_path):
        """Start transcription worker when button is clicked."""
        self.step1.transcribe_btn.setEnabled(False)
        self.step1.progress_bar.setValue(0)
        self._current_video_path = file_path

        model = self._settings.get("model", "large")
        force_cpu = self._settings.get("force_cpu", False)
        self._transcription_worker = TranscriptionWorker(file_path, model=model, force_cpu=force_cpu)
        self._transcription_worker.progress.connect(self.step1.set_progress_with_stage)
        self._transcription_worker.finished.connect(self._on_transcription_finished)
        self._transcription_worker.error.connect(self._on_transcription_error)
        self._transcription_worker.start()

    def _on_transcription_finished(self, json_path):
        """Handle successful transcription."""
        self._current_json_path = json_path
        self.step1.stop_shimmer()
        self.step1.progress_bar.setVisible(False)
        self.step1.progress_label.setVisible(False)
        self._step2_typing_played = False

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
            self.step2.populate_chunks(chunk_data, self._current_video_path)

            # Load audio into the audio player
            self.audio.load_audio(self._current_video_path)

            # Enable step 2 if first time, otherwise just switch to it
            if 2 in self.tab_bar.disabled_steps:
                self.tab_bar.enable_step(2, on_complete=lambda: self._show_step(2))
            else:
                self._show_step(2)

        except Exception as e:
            self._on_transcription_error(f"Failed to process transcription: {str(e)}")

    def _on_transcription_error(self, error_msg):
        """Handle transcription error."""
        logger.error(f"Transcription error: {error_msg}")
        self.step1.stop_shimmer()
        self.step1.transcribe_btn.setEnabled(True)
        self.step1.progress_bar.setVisible(False)
        self.step1.progress_label.setVisible(False)

    def _merge_chunks_by_time(self, original_chunks, manually_added_chunks):
        """Merge original and manually added chunks, sorted by start time."""
        chunk_list = []

        debug_logger.debug(f"Merging {len(original_chunks)} original chunks with {len(manually_added_chunks)} manual chunks")

        for i, chunk in enumerate(original_chunks):
            if chunk and chunk[0]:
                start_time = chunk[0][0].start
                chunk_list.append((start_time, 'original', i, chunk))
                debug_logger.debug(f"  Original chunk {i}: start={start_time:.3f}s")

        for i, chunk in enumerate(manually_added_chunks):
            if chunk and chunk[0]:
                start_time = chunk[0][0].start
                chunk_list.append((start_time, 'manual', i, chunk))
                debug_logger.debug(f"  Manual chunk {i}: start={start_time:.3f}s")

        chunk_list.sort(key=lambda x: x[0])
        debug_logger.debug(f"After sorting, first 5 chunks:")
        for i, (start_time, chunk_type, idx, _) in enumerate(chunk_list[:5]):
            debug_logger.debug(f"  Position {i}: {chunk_type} chunk {idx} at {start_time:.3f}s")

        return [chunk for _, _, _, chunk in chunk_list]

    def _on_generation_started(self):
        """Generate comp from edited chunks."""
        # Stop typing animation and populate all text immediately
        self.step2.stop_animation_and_populate()

        try:
            if not self._current_json_path:
                self.step2.result_label.setText("Error: No transcription data")
                return

            # Load original words
            words = load_whisper_json(self._current_json_path)

            # Get edited chunks and flags (includes manual chunks)
            edited_chunks_all = self.step2.get_edited_chunks()
            edited_flags_all = self.step2.get_edited_flags()
            manual_timestamps = self.step2.get_manual_chunk_timestamps()
            deleted_timestamps = self.step2.get_deleted_chunk_timestamps()

            # Extract ONLY original chunks - skip manual chunks and deleted chunks
            edited_chunks = []
            edited_flags = []
            for i, (ts, text) in enumerate(edited_chunks_all):
                ts_float = float(ts)
                is_manual = any(abs(ts_float - mt) < 0.001 for mt in manual_timestamps)
                is_deleted = ts in deleted_timestamps
                if not is_manual and not is_deleted:
                    edited_chunks.append((ts, text))
                    edited_flags.append(edited_flags_all[i])

            debug_logger.debug(f"Passing to rebuild: {len(edited_chunks)} edited chunks (excluded {len(manual_timestamps)} manual, {len(deleted_timestamps)} deleted)")

            # Filter _original_chunks to remove deleted ones before rebuilding
            filtered_original_chunks = [chunk for chunk in self._original_chunks
                                       if not any(abs(chunk[0][0].start - float(ts)) < 0.001 for ts in deleted_timestamps)]

            # Rebuild with ONLY original non-deleted chunks
            rebuilt_original_chunks = rebuild_chunks_with_edits(filtered_original_chunks, edited_chunks, edited_flags)

            # Now merge the rebuilt original chunks with manually added chunks, sorted by time
            manually_added = self.step2.get_manually_added_chunks()
            rebuilt_chunks = self._merge_chunks_by_time(rebuilt_original_chunks, manually_added)

            # Log first few chunks before comp generation
            debug_logger.debug(f"Final rebuilt_chunks: {len(rebuilt_chunks)} total")
            for i in range(min(5, len(rebuilt_chunks))):
                chunk = rebuilt_chunks[i]
                if chunk and chunk[0] and chunk[0][0]:
                    start = chunk[0][0].start
                    all_w = []
                    for line in chunk:
                        all_w.extend(line)
                    text = " ".join([w.text for w in all_w[:3]])
                    debug_logger.debug(f"  Position {i}: start={start:.3f}s, text={text}")

            # Generate comp
            debug_logger.debug(f"Generating comp from {len(rebuilt_chunks)} chunks")
            template = self._settings.get("template", "Zeta Reticuli Template.comp")
            fps = self._settings.get("fps", 24)
            comp_content = generate_single_comp(rebuilt_chunks, fps=fps, pause_threshold=0.3, template_name=template)
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
                self.step2.generate_btn.setEnabled(True)
                self.step2.result_label.setText(f"✓ Generated: {output_path.name}")
            else:
                debug_logger.debug("User cancelled comp save")
                self.step2.generate_btn.setEnabled(True)
                self.step2.result_label.setText("Cancelled")

        except Exception as e:
            self.step2.generate_btn.setEnabled(True)
            self.step2.result_label.setText(f"Error: {str(e)}")

    def _on_settings_changed(self, settings):
        """Handle settings change."""
        self._settings = settings
        save_settings(settings)
        logger.info(f"Settings updated: model={settings['model']}, force_cpu={settings['force_cpu']}, template={settings['template']}")

    def eventFilter(self, obj, event):
        """Capture keyboard events for global audio player control."""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()

            # Don't intercept if focus is on a text input widget
            from PyQt6.QtWidgets import QLineEdit, QTextEdit
            focused_widget = QApplication.focusWidget()
            is_text_input = isinstance(focused_widget, (QLineEdit, QTextEdit))

            # Arrow keys should only be handled if not in a text box
            if key in (Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                if is_text_input:
                    return False  # Let text input handle it

            if key in (Qt.Key.Key_Space, Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_I, Qt.Key.Key_O):
                if self.audio.isVisible() and not is_text_input:
                    self.audio.keyPressEvent(event)
                    if event.isAccepted():
                        return True
        return super().eventFilter(obj, event)

    def closeEvent(self, event):
        """Clean up temporary JSON file when closing."""
        if self._current_json_path:
            try:
                Path(self._current_json_path).unlink()
                logger.info("Cleaned up temporary JSON file")
            except Exception as e:
                logger.warning(f"Could not delete temp JSON: {e}")
        event.accept()

    def _show_step(self, step):
        self.tab_bar.set_active(step, animate=True)

        # Audio player shows with step 2
        if step == 2:
            self.audio.setVisible(True)
        else:
            self.audio.setVisible(False)

        # Map step to widget and effect
        widgets = {1: self.step1, 2: self.step2, 3: self.settings}
        effects = {1: self.step1_effect, 2: self.step2_effect, 3: self.settings_effect}

        incoming = widgets[step]
        in_effect = effects[step]

        # Find currently visible widget
        outgoing = None
        out_effect = None
        for s, w in widgets.items():
            if w.isVisible():
                outgoing = w
                out_effect = effects[s]
                break

        # If no widget is currently visible, just show the incoming one
        if outgoing is None:
            incoming.setVisible(True)
            in_effect.setOpacity(1.0)
            if step == 2:
                self.audio.setVisible(True)
                self.audio_effect.setOpacity(1.0)
                self.step2.restart_typing()
            elif step == 3:
                self.settings.set_settings(self._settings["model"], self._settings["force_cpu"], self._settings.get("template", "Zeta Reticuli Template.comp"), self._settings.get("fps", 24))
            return

        # If the incoming widget is already visible, don't animate
        if incoming is outgoing:
            return

        # Fade out current, fade in new
        fade_out = QPropertyAnimation(out_effect, b"opacity")
        fade_out.setDuration(150)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_fade_out_done():
            outgoing.setVisible(False)
            # Fade out audio player if not step 2
            if step != 2 and self.audio.isVisible():
                audio_fade_out = QPropertyAnimation(self.audio_effect, b"opacity")
                audio_fade_out.setDuration(150)
                audio_fade_out.setStartValue(1.0)
                audio_fade_out.setEndValue(0.0)
                audio_fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)
                audio_fade_out.finished.connect(lambda: self.audio.setVisible(False))
                audio_fade_out.start()
                self._audio_fade_out_anim = audio_fade_out

            incoming.setVisible(True)
            fade_in = QPropertyAnimation(in_effect, b"opacity")
            fade_in.setDuration(150)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InCubic)
            fade_in.start()
            self._fade_in_anim = fade_in

            # Fade in audio player if step 2
            if step == 2:
                self.audio.setVisible(True)
                self.audio.setFocus()
                audio_fade_in = QPropertyAnimation(self.audio_effect, b"opacity")
                audio_fade_in.setDuration(150)
                audio_fade_in.setStartValue(0.0)
                audio_fade_in.setEndValue(1.0)
                audio_fade_in.setEasingCurve(QEasingCurve.Type.InCubic)
                audio_fade_in.start()
                self._audio_fade_in_anim = audio_fade_in

            if step == 2 and not self._step2_typing_played:
                self.step2.restart_typing()
                self._step2_typing_played = True
            elif step == 3:
                self.settings.set_settings(self._settings["model"], self._settings["force_cpu"], self._settings.get("template", "Zeta Reticuli Template.comp"), self._settings.get("fps", 24))

        fade_out.finished.connect(on_fade_out_done)
        self._fade_out_anim = fade_out
        fade_out.start()
