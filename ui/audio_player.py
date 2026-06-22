"""Audio player widget for timing reference."""
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSlider
)
from PyQt6.QtCore import Qt, QTimer, QUrl, QByteArray, QSize, QEvent
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer

logger = logging.getLogger(__name__)
debug_logger = logging.getLogger(f"{__name__}.debug")


class CustomSlider(QSlider):
    """Slider that doesn't consume arrow keys so AudioPlayerWidget can handle them."""
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            # Don't handle arrow keys - let parent handle them
            event.ignore()
        else:
            super().keyPressEvent(event)


class AudioPlayerWidget(QGroupBox):
    def __init__(self):
        super().__init__("Audio Player")
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        self._current_file = None
        self._build_ui()
        self._setup_timer()
        # Install event filter to capture keyboard events globally
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Capture keyboard events for scrubbing and play/pause."""
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Left, Qt.Key.Key_Right, Qt.Key.Key_Up, Qt.Key.Key_Down):
                return self.keyPressEvent(event) or False
        return super().eventFilter(obj, event)

    def _build_ui(self):
        # Make widget focusable so it can receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        layout = QVBoxLayout()
        layout.setSpacing(16)

        # Title
        title = QLabel("Play audio to find exact timestamps for new chunks")
        title_font = QFont()
        title_font.setPointSize(11)
        title.setFont(title_font)
        title.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(title)

        # Timeline display
        timeline_layout = QHBoxLayout()
        self.time_label = QLabel("00:00.000")
        self.time_label.setStyleSheet("color: #00ff88; font-weight: bold; font-size: 14px;")
        self.time_label.setMinimumWidth(100)
        timeline_layout.addWidget(self.time_label)
        timeline_layout.addStretch()
        layout.addLayout(timeline_layout)

        # Slider
        self.slider = CustomSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.setSingleStep(25)    # 25ms step for precise control
        self.slider.setPageStep(25)      # 25ms per scroll wheel click
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.valueChanged.connect(self._on_slider_value_changed)  # Handle scroll wheel and keyboard
        layout.addWidget(self.slider)

        # Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)

        # Create play icon from SVG
        play_svg = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 5v14l11-7z" fill="#00ff88"/>
        </svg>'''
        play_icon = self._create_icon_from_svg(play_svg)

        self.play_btn = QPushButton()
        self.play_btn.setIcon(play_icon)
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setFixedHeight(40)
        self.play_btn.setFixedWidth(50)
        self.play_btn.clicked.connect(self._on_play_clicked)
        self.play_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #00ff88;
                border-radius: 3px;
            }
            QPushButton:hover:!disabled {
                background-color: #2a2a2a;
                border: 1px solid #00ffaa;
            }
            QPushButton:pressed:!disabled {
                background-color: #0a1a0a;
            }
            QPushButton:disabled {
                border: 1px solid #555555;
            }
        """)
        controls_layout.addWidget(self.play_btn)

        # Create pause icon from SVG
        pause_svg = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="6" y="4" width="3" height="16" fill="#00ff88"/>
            <rect x="15" y="4" width="3" height="16" fill="#00ff88"/>
        </svg>'''
        pause_icon = self._create_icon_from_svg(pause_svg)

        self.pause_btn = QPushButton()
        self.pause_btn.setIcon(pause_icon)
        self.pause_btn.setIconSize(QSize(24, 24))
        self.pause_btn.setFixedHeight(40)
        self.pause_btn.setFixedWidth(50)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                border: 1px solid #00ff88;
                border-radius: 3px;
            }
            QPushButton:hover:!disabled {
                background-color: #2a2a2a;
                border: 1px solid #00ffaa;
            }
            QPushButton:pressed:!disabled {
                background-color: #0a1a0a;
            }
            QPushButton:disabled {
                border: 1px solid #555555;
            }
        """)
        controls_layout.addWidget(self.pause_btn)

        controls_layout.addStretch()
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
        from PyQt6.QtGui import QPainter
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
        # Update time label immediately when dragging
        self._update_time_label()
        # Play brief audio feedback when user releases from dragging
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()
            QTimer.singleShot(50, self._player.pause)

    def _on_slider_value_changed(self, position):
        """Handle slider value changes (scroll wheel, keyboard)."""
        self._player.setPosition(position)
        self._update_time_label()
        # Play brief snippet for each scroll - overlaps on fast scrolling (like DaVinci)
        if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            self._player.play()
            QTimer.singleShot(25, self._player.pause)

    def _on_position_changed(self, position):
        """Update slider when playback position changes."""
        self.slider.blockSignals(True)
        self.slider.setValue(position)
        self.slider.blockSignals(False)

    def _on_duration_changed(self, duration):
        """Update slider max when duration is known."""
        self.slider.setMaximum(duration)

    def _update_time_label(self):
        """Update time label with current position."""
        position_ms = self._player.position()
        seconds = position_ms / 1000
        minutes = int(seconds) // 60
        secs = int(seconds) % 60
        millis = int(position_ms % 1000)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}.{millis:03d}")

    def stop(self):
        """Stop playback and cleanup."""
        self._player.stop()
        self.timer.stop()
        self.play_btn.setEnabled(False if not self._current_file else True)
        self.pause_btn.setEnabled(False)

    def keyPressEvent(self, event):
        """Handle global keyboard shortcuts for audio control."""
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            # Space bar: toggle play/pause
            if self._current_file:
                if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self._on_pause_clicked()
                else:
                    self._on_play_clicked()
            return True
        elif event.key() == Qt.Key.Key_Left:
            # Left arrow: scrub backward by 25ms
            if self._current_file:
                new_pos = max(0, self._player.position() - 25)
                self._player.setPosition(new_pos)
                self._update_time_label()
                # Play brief snippet for audio feedback
                if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self._player.play()
                    QTimer.singleShot(25, self._player.pause)
            return True
        elif event.key() == Qt.Key.Key_Right:
            # Right arrow: scrub forward by 25ms
            if self._current_file:
                new_pos = min(self._player.duration(), self._player.position() + 25)
                self._player.setPosition(new_pos)
                self._update_time_label()
                # Play brief snippet for audio feedback
                if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self._player.play()
                    QTimer.singleShot(25, self._player.pause)
            return True
        elif event.key() == Qt.Key.Key_Up:
            # Up arrow: scrub forward by 10ms
            if self._current_file:
                new_pos = min(self._player.duration(), self._player.position() + 10)
                self._player.setPosition(new_pos)
                self._update_time_label()
                # Play brief snippet for audio feedback
                if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self._player.play()
                    QTimer.singleShot(10, self._player.pause)
            return True
        elif event.key() == Qt.Key.Key_Down:
            # Down arrow: scrub backward by 10ms
            if self._current_file:
                new_pos = max(0, self._player.position() - 10)
                self._player.setPosition(new_pos)
                self._update_time_label()
                # Play brief snippet for audio feedback
                if self._player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                    self._player.play()
                    QTimer.singleShot(10, self._player.pause)
            return True
        return super().keyPressEvent(event)
