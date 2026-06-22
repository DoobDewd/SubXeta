"""Audio player widget for timing reference."""
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QByteArray, QSize, QEvent, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPen
from PyQt6.QtSvg import QSvgRenderer
from ui import theme

logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")


class CustomSlider(QSlider):
    """Slider that shows In/Out range highlight and playhead line."""

    in_set = pyqtSignal(int)  # Emitted when In is set
    out_set = pyqtSignal(int)  # Emitted when Out is set

    def __init__(self, orientation=Qt.Orientation.Horizontal):
        super().__init__(orientation)
        self.in_marker = 0  # In point position (ms)
        self.out_marker = 0  # Out point position (ms)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """Show context menu for setting In/Out."""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        in_action = menu.addAction("Set In Point")
        out_action = menu.addAction("Set Out Point")

        action = menu.exec(self.mapToGlobal(pos))

        if action == in_action:
            self.in_set.emit(self.value())
        elif action == out_action:
            self.out_set.emit(self.value())

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            # Don't handle arrow keys - let parent handle them
            event.ignore()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        """Draw slider with range highlight and In/Out marker lines."""
        super().paintEvent(event)

        painter = QPainter(self)

        # Draw semi-transparent range highlight
        if self.maximum() > 0 and self.in_marker < self.out_marker:
            in_x = self._value_to_pixel(self.in_marker)
            out_x = self._value_to_pixel(self.out_marker)

            # Semi-transparent green rectangle for In/Out range
            range_rect_y = self.height() // 4
            range_rect_height = self.height() // 2
            painter.fillRect(int(in_x), range_rect_y, int(out_x - in_x), range_rect_height,
                           QColor(*theme.GREEN_RGB, 50))  # Green with alpha

            # Draw In marker line (theme green) on the slider
            pen = QPen(QColor(*theme.GREEN_RGB))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(int(in_x), 0, int(in_x), self.height())

            # Draw Out marker line (theme green) on the slider
            painter.drawLine(int(out_x), 0, int(out_x), self.height())

        painter.end()

    def _value_to_pixel(self, value):
        """Convert slider value to pixel position."""
        if self.maximum() == 0:
            return 0
        # Linear mapping - offset applied in paintEvent
        return (value / self.maximum()) * (self.width() - 1)


class InOutKnobControl(QWidget):
    """Control widget with draggable In/Out knobs below the slider."""

    in_changed = pyqtSignal(int)  # Emitted when In knob moves
    out_changed = pyqtSignal(int)  # Emitted when Out knob moves

    def __init__(self, parent=None):
        super().__init__(parent)
        self.in_value = 0
        self.out_value = 0
        self.max_value = 0
        self._dragging = None  # 'in' or 'out'
        self.slider = None  # Reference to slider for width calculations
        self.setFixedHeight(40)

    def set_values(self, in_val, out_val, max_val):
        """Set the knob positions and maximum value."""
        self.in_value = in_val
        self.out_value = out_val
        self.max_value = max_val
        self.update()

    def mousePressEvent(self, event):
        """Handle clicks on knobs."""
        if event.button() == Qt.MouseButton.LeftButton:
            in_x = self._value_to_pixel(self.in_value)
            out_x = self._value_to_pixel(self.out_value)

            # Check if clicking on In knob (with tolerance)
            if abs(event.pos().x() - in_x) < 15:
                self._dragging = 'in'
                event.accept()
                return

            # Check if clicking on Out knob (with tolerance)
            if abs(event.pos().x() - out_x) < 15:
                self._dragging = 'out'
                event.accept()
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle dragging knobs."""
        if self._dragging:
            pos = self._get_value_from_pixel(event.pos().x())

            if self._dragging == 'in':
                self.in_value = max(0, min(pos, self.out_value - 1))
                self.in_changed.emit(self.in_value)
            else:  # 'out'
                self.out_value = max(self.in_value + 1, min(pos, self.max_value))
                self.out_changed.emit(self.out_value)

            self.update()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Stop dragging."""
        self._dragging = None
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        """Draw In/Out knobs with short vertical lines."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setClipping(False)  # Allow drawing outside widget bounds

        knob_radius = 8
        knob_y = self.height() // 2
        theme_green = QColor(*theme.GREEN_RGB)
        knob_border = QColor(*theme.GREEN_KNOB_BORDER_RGB)
        line_height = 8  # Short line above knob

        if self.max_value > 0:
            # Draw In knob with line
            in_x = int(self._value_to_pixel(self.in_value))
            # Draw short vertical line above knob
            pen = QPen(theme_green)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(in_x, knob_y - knob_radius - line_height, in_x, knob_y - knob_radius)
            # Draw knob
            painter.setBrush(theme_green)
            painter.setPen(knob_border)  # Darker green for border
            painter.drawEllipse(in_x - knob_radius, knob_y - knob_radius,
                              knob_radius * 2, knob_radius * 2)

            # Draw Out knob with line
            out_x = int(self._value_to_pixel(self.out_value))
            # Draw short vertical line above knob
            pen = QPen(theme_green)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawLine(out_x, knob_y - knob_radius - line_height, out_x, knob_y - knob_radius)
            # Draw knob
            painter.setBrush(theme_green)
            painter.setPen(knob_border)  # Darker green for border
            painter.drawEllipse(out_x - knob_radius, knob_y - knob_radius,
                              knob_radius * 2, knob_radius * 2)

        painter.end()

    def _value_to_pixel(self, value):
        """Convert value to pixel position."""
        if self.max_value == 0:
            return 0
        # Use slider's width for consistent positioning
        width = self.slider.width() if self.slider else self.width()
        # Linear mapping - offset applied in paintEvent
        return (value / self.max_value) * (width - 1)

    def _get_value_from_pixel(self, pixel_x):
        """Convert pixel position to value."""
        if self.max_value == 0:
            return 0
        # Use slider's width for consistent positioning
        width = self.slider.width() if self.slider else self.width()
        if width <= 0:
            return 0
        pixel_pos = max(0, min(pixel_x, width))
        return int((pixel_pos / width) * self.max_value)


class AudioPlayerWidget(QGroupBox):
    # Signal to request adding a chunk with specific times
    add_chunk_requested = pyqtSignal(float, float)  # (start_time, end_time)

    def __init__(self):
        super().__init__("Audio Player")
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._current_file = None
        self._build_ui()
        self._setup_timer()

    def _build_ui(self):
        # Make widget focusable so it can receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 12, 0, 0)

        # Title
        title = QLabel("Play audio to find exact timestamps for new segments")
        title_font = QFont()
        title_font.setPointSize(11)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {theme.TEXT}; background-color: transparent;")
        layout.addWidget(title)

        # Timeline display
        timeline_layout = QHBoxLayout()
        self.time_label = QLabel("00:00.000")
        self.time_label.setStyleSheet(f"color: {theme.GREEN}; font-weight: bold; font-size: 14px; background-color: transparent;")
        self.time_label.setMinimumWidth(100)
        timeline_layout.addWidget(self.time_label)
        timeline_layout.addStretch()
        layout.addLayout(timeline_layout)

        # Slider
        self.slider = CustomSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setSingleStep(25)
        self.slider.setPageStep(25)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.valueChanged.connect(self._on_slider_value_changed)
        self.slider.in_set.connect(self._on_set_in_point)
        self.slider.out_set.connect(self._on_set_out_point)
        layout.addWidget(self.slider)

        # In/Out knob controls with connecting lines
        self.knob_control = InOutKnobControl()
        self.knob_control.slider = self.slider  # Reference slider for width calculations
        self.knob_control.in_changed.connect(self._on_in_changed)
        self.knob_control.out_changed.connect(self._on_out_changed)
        layout.addWidget(self.knob_control)

        # In/Out time display
        inout_display_layout = QHBoxLayout()
        inout_display_layout.setSpacing(12)
        inout_display_layout.setContentsMargins(0, 0, 0, 0)

        in_label = QLabel("In:")
        in_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 10px; background-color: transparent;")
        inout_display_layout.addWidget(in_label)

        self.in_time_label = QLineEdit("0.000")
        self.in_time_label.setStyleSheet(f"""
            QLineEdit {{
                color: {theme.GREEN};
                font-weight: bold;
                border: 1px solid {theme.GREEN};
                padding: 4px 8px;
                border-radius: 4px;
                background-color: transparent;
            }}
            QLineEdit:focus {{
                background-color: {theme.BG_FOCUS};
                border: 2px solid {theme.GREEN_BRIGHT};
            }}
        """)
        self.in_time_label.setMaximumWidth(100)
        self.in_time_label.editingFinished.connect(self._on_in_time_edited)
        inout_display_layout.addWidget(self.in_time_label)

        out_label = QLabel("Out:")
        out_label.setStyleSheet(f"color: {theme.TEXT_MUTED}; font-size: 10px; background-color: transparent;")
        inout_display_layout.addWidget(out_label)

        self.out_time_label = QLineEdit("0.000")
        self.out_time_label.setStyleSheet(f"""
            QLineEdit {{
                color: {theme.GREEN};
                font-weight: bold;
                border: 1px solid {theme.GREEN};
                padding: 4px 8px;
                border-radius: 4px;
                background-color: transparent;
            }}
            QLineEdit:focus {{
                background-color: {theme.BG_FOCUS};
                border: 2px solid {theme.GREEN_BRIGHT};
            }}
        """)
        self.out_time_label.setMaximumWidth(100)
        self.out_time_label.editingFinished.connect(self._on_out_time_edited)
        inout_display_layout.addWidget(self.out_time_label)

        inout_display_layout.addStretch()
        layout.addLayout(inout_display_layout)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Play button
        play_svg = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5v14l11-7z" fill="{theme.GREEN}"/>
        </svg>'''
        play_svg_hover = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5v14l11-7z" fill="{theme.GREEN_HOVER}"/>
        </svg>'''
        play_icon = self._create_icon_from_svg(play_svg)
        play_icon_hover = self._create_icon_from_svg(play_svg_hover)

        self.play_btn = QPushButton()
        self.play_btn.setIcon(play_icon)
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setFixedHeight(40)
        self.play_btn.setFixedWidth(50)
        self.play_btn.clicked.connect(self._on_play_clicked)
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)

        # Store icons and sizes for hover effect
        self.play_btn._normal_icon = play_icon
        self.play_btn._hover_icon = play_icon_hover
        self.play_btn._normal_size = QSize(24, 24)
        self.play_btn._hover_size = QSize(28, 28)

        def on_play_hover_enter():
            if self.play_btn.isEnabled():
                self.play_btn.setIcon(self.play_btn._hover_icon)
                self.play_btn.setIconSize(self.play_btn._hover_size)

        def on_play_hover_leave():
            self.play_btn.setIcon(self.play_btn._normal_icon)
            self.play_btn.setIconSize(self.play_btn._normal_size)

        self.play_btn.enterEvent = lambda e: on_play_hover_enter()
        self.play_btn.leaveEvent = lambda e: on_play_hover_leave()
        controls_layout.addWidget(self.play_btn)

        # Pause button
        pause_svg = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="4" width="3" height="16" fill="{theme.GREEN}"/>
            <rect x="15" y="4" width="3" height="16" fill="{theme.GREEN}"/>
        </svg>'''
        pause_svg_hover = f'''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="4" width="3" height="16" fill="{theme.GREEN_HOVER}"/>
            <rect x="15" y="4" width="3" height="16" fill="{theme.GREEN_HOVER}"/>
        </svg>'''
        pause_icon = self._create_icon_from_svg(pause_svg)
        pause_icon_hover = self._create_icon_from_svg(pause_svg_hover)

        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(pause_icon)
        self.pause_btn.setIconSize(QSize(24, 24))
        self.pause_btn.setFixedHeight(40)
        self.pause_btn.setFixedWidth(50)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QPushButton:disabled {
                opacity: 0.5;
            }
        """)

        # Store icons and sizes for hover effect
        self.pause_btn._normal_icon = pause_icon
        self.pause_btn._hover_icon = pause_icon_hover
        self.pause_btn._normal_size = QSize(24, 24)
        self.pause_btn._hover_size = QSize(28, 28)

        def on_pause_hover_enter():
            if self.pause_btn.isEnabled():
                self.pause_btn.setIcon(self.pause_btn._hover_icon)
                self.pause_btn.setIconSize(self.pause_btn._hover_size)

        def on_pause_hover_leave():
            self.pause_btn.setIcon(self.pause_btn._normal_icon)
            self.pause_btn.setIconSize(self.pause_btn._normal_size)

        self.pause_btn.enterEvent = lambda e: on_pause_hover_enter()
        self.pause_btn.leaveEvent = lambda e: on_pause_hover_leave()
        controls_layout.addWidget(self.pause_btn)

        controls_layout.addStretch()

        # Add Chunk button
        self.add_chunk_btn = QPushButton("Add Segment")
        self.add_chunk_btn.setFixedHeight(32)
        self.add_chunk_btn.setFixedWidth(100)
        self.add_chunk_btn.clicked.connect(self._on_add_chunk_clicked)
        self.add_chunk_btn.setEnabled(False)
        self.add_chunk_btn.setStyleSheet("QPushButton { padding: 2px 4px; margin: 0px; }")
        controls_layout.addWidget(self.add_chunk_btn)

        layout.addLayout(controls_layout)
        layout.addStretch()
        self.setLayout(layout)

        # Connect player signals
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

    def _setup_timer(self):
        """Setup timer for UI updates."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time_label)

    def _create_icon_from_svg(self, svg_string):
        """Create a QIcon from SVG string."""
        svg_bytes = QByteArray(svg_string.encode('utf-8'))
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return QIcon(pixmap)

    def showEvent(self, event):
        """Take focus when shown so keyboard events reach us."""
        super().showEvent(event)
        self.setFocus()

    def load_audio(self, file_path):
        """Load audio file for playback."""
        if not file_path:
            return

        path = Path(file_path)
        if path.exists():
            self._current_file = str(path)
            self._player.setSource(QUrl.fromLocalFile(self._current_file))
            self.play_btn.setEnabled(True)
            self.add_chunk_btn.setEnabled(True)
            debug_logger.debug(f"Audio loaded: {self._current_file}")
        else:
            debug_logger.debug(f"Audio file not found: {file_path}")

    def _on_play_clicked(self):
        """Play audio."""
        if self._current_file:
            self._player.play()
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.timer.start(100)

    def _on_pause_clicked(self):
        """Pause audio."""
        self._player.pause()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.timer.stop()

    def _on_slider_moved(self, position):
        """Handle slider movement (mouse drag)."""
        self._player.setPosition(position)
        self._update_time_label()
        # Play brief audio feedback when user releases from dragging
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()
            QTimer.singleShot(50, self._player.pause)

    def _on_slider_value_changed(self, position):
        """Handle slider value changes (scroll wheel, keyboard)."""
        self._player.setPosition(position)
        self._update_time_label()
        # Play brief snippet for each scroll - overlaps on fast scrolling
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()
            QTimer.singleShot(25, self._player.pause)

    def _on_position_changed(self, position):
        """Update slider when playback position changes."""
        self.slider.blockSignals(True)
        self.slider.setValue(position)
        self.slider.blockSignals(False)
        self.slider.update()  # Redraw playhead line

    def _on_duration_changed(self, duration):
        """Update slider max when duration is known."""
        self.slider.setMaximum(duration)
        # Set Out marker to end of audio
        self.slider.out_marker = duration
        self.knob_control.set_values(0, duration, duration)
        self._update_out_label()
        self.slider.update()
        self.knob_control.update()

    def _on_in_changed(self, value):
        """Handle In knob moved."""
        self.slider.in_marker = value
        self._update_in_label()
        self.slider.update()
        self.knob_control.update()

    def _on_out_changed(self, value):
        """Handle Out knob moved."""
        self.slider.out_marker = value
        self._update_out_label()
        self.slider.update()
        self.knob_control.update()

    def _update_time_label(self):
        """Update current time label."""
        position_ms = self._player.position()
        seconds = position_ms / 1000
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        millis = int(position_ms % 1000)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}.{millis:03d}")

    def _update_in_label(self):
        """Update In time label."""
        pos_ms = self.slider.in_marker
        seconds = pos_ms / 1000
        self.in_time_label.setText(f"{seconds:.3f}")

    def _update_out_label(self):
        """Update Out time label."""
        pos_ms = self.slider.out_marker
        seconds = pos_ms / 1000
        self.out_time_label.setText(f"{seconds:.3f}")

    def _on_in_time_edited(self):
        """Handle user editing In time field."""
        try:
            time_text = self.in_time_label.text()
            # Parse seconds.milliseconds format (e.g., "1.234")
            seconds = float(time_text)
            total_ms = int(seconds * 1000)

            # Clamp to valid range
            total_ms = max(0, min(total_ms, self.slider.out_marker - 1))

            self.slider.in_marker = total_ms
            self.knob_control.in_changed.emit(total_ms)
            self._update_in_label()
        except ValueError:
            # Invalid input, revert to current value
            self._update_in_label()

    def _on_out_time_edited(self):
        """Handle user editing Out time field."""
        try:
            time_text = self.out_time_label.text()
            # Parse seconds.milliseconds format (e.g., "1.234")
            seconds = float(time_text)
            total_ms = int(seconds * 1000)

            # Clamp to valid range
            total_ms = max(self.slider.in_marker + 1, min(total_ms, self.slider.maximum()))

            self.slider.out_marker = total_ms
            self.knob_control.out_changed.emit(total_ms)
            self._update_out_label()
        except ValueError:
            # Invalid input, revert to current value
            self._update_out_label()

    def _on_add_chunk_clicked(self):
        """Emit signal to add chunk with In/Out times."""
        if self.slider.in_marker < self.slider.out_marker:
            self.add_chunk_requested.emit(self.slider.in_marker / 1000, self.slider.out_marker / 1000)

    def stop(self):
        """Stop playback and cleanup."""
        self._player.stop()
        self.timer.stop()
        self.play_btn.setEnabled(False if not self._current_file else True)
        self.pause_btn.setEnabled(False)

    def _on_set_in_point(self, value=None):
        """Set In point to current playhead position."""
        # Use slider value if no value provided, otherwise use player position
        pos = self.slider.value() if value is None else value
        self.slider.in_marker = pos
        self.knob_control.in_value = pos
        self._update_in_label()
        self.slider.update()
        self.knob_control.update()

    def _on_set_out_point(self, value=None):
        """Set Out point to current playhead position."""
        # Use slider value if no value provided, otherwise use player position
        pos = self.slider.value() if value is None else value
        self.slider.out_marker = pos
        self.knob_control.out_value = pos
        self._update_out_label()
        self.slider.update()
        self.knob_control.update()

    def _scrub(self, delta_ms):
        """Move the playhead by delta_ms (clamped to the clip), with a brief
        audio snippet for feedback. Snippet length scales with the scrub step."""
        if not self._current_file:
            return
        new_pos = max(0, min(self._player.duration(), self._player.position() + delta_ms))
        self._player.setPosition(new_pos)
        self._update_time_label()
        # Play brief snippet for audio feedback
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()
            QTimer.singleShot(abs(delta_ms), self._player.pause)

    def keyPressEvent(self, event):
        """Handle global keyboard shortcuts for audio control."""
        if event.key() == Qt.Key.Key_Space:
            # Space bar: toggle play/pause
            debug_logger.debug(f"Space pressed, _current_file={self._current_file}, file exists={bool(self._current_file)}")
            if self._current_file:
                if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self._on_pause_clicked()
                else:
                    self._on_play_clicked()
            event.accept()
            return
        elif event.key() == Qt.Key.Key_I:
            # I key: set In point
            self._on_set_in_point(self._player.position())
            event.accept()
            return
        elif event.key() == Qt.Key.Key_O:
            # O key: set Out point
            self._on_set_out_point(self._player.position())
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Left:
            self._scrub(-25)  # Left: scrub backward 25ms
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Right:
            self._scrub(25)  # Right: scrub forward 25ms
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Up:
            self._scrub(10)  # Up: scrub forward 10ms
            event.accept()
            return
        elif event.key() == Qt.Key.Key_Down:
            self._scrub(-10)  # Down: scrub backward 10ms
            event.accept()
            return
        super().keyPressEvent(event)
