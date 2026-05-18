"""Custom tab bar with sliding underline indicator."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor
from ui.animations import TypingAnimator


class TabBar(QWidget):
    """Custom tab bar with sliding underline."""
    tab_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(50)
        self.setStyleSheet("background-color: #1a1a1a;")

        layout = QHBoxLayout()
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(48)

        self.labels = []
        self.active_step = 1
        self.anim = None
        self._underline_x = 0
        self._underline_width = 0
        self._underline_opacity = 1.0
        self.disabled_steps = {2}
        self._typing_animator = TypingAnimator(char_delay_ms=25)
        self._first_show = True

        for i, text in enumerate(["Transcribe Audio", "Review & Generate"]):
            label = QLabel("")  # Both start empty for animation
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setContentsMargins(0, 0, 0, 0)
            label.setMaximumHeight(28)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            label.step = i + 1
            label.full_text = text
            label.mousePressEvent = lambda e, s=i+1: self.on_tab_click(s)
            label.setVisible(i == 0)  # Hide Step 2 initially
            self.labels.append(label)
            layout.addWidget(label)

        layout.addStretch()
        self.setLayout(layout)

    def showEvent(self, event):
        """Initialize and animate Step 1 text in on first show only."""
        super().showEvent(event)
        if self._first_show:
            # Animate Step 1 text in with fade-in underline only on first show
            step1_label = self.labels[0]
            self._animate_label_text_in(step1_label, fade_in=True)
            self._first_show = False

    def on_tab_click(self, step):
        if step in self.disabled_steps:
            return
        self.set_active(step, animate=True)
        self.tab_changed.emit(step)

    def enable_step(self, step, on_complete=None):
        """Enable a previously disabled step and animate text in."""
        if step in self.disabled_steps:
            self.disabled_steps.remove(step)
            label = self.labels[step - 1]
            # Ensure underline is on Step 1 before showing Step 2
            self.set_active(1, animate=False)
            label.setVisible(True)
            # Start typing animation for the label, targeting Step 2 when done
            self._animate_label_text_in(label, on_complete, target_step=step)

    def _animate_label_text_in(self, label, on_complete=None, target_step=None, fade_in=False):
        """Animate text typing in for a label."""
        full_text = label.full_text
        step_num = label.step if hasattr(label, 'step') else 1
        target = target_step if target_step is not None else step_num

        def on_typing_done():
            if fade_in:
                self.set_active(target, animate=False)
                self._fade_in_underline()
            else:
                self.set_active(target, animate=True)
            if on_complete:
                on_complete()

        self._typing_animator.animate_single(label, full_text, on_typing_done)

    def _fade_in_underline(self):
        """Fade in the underline opacity."""
        self._underline_opacity = 0.0

        def fade_tick():
            self._underline_opacity += 0.1
            self.update()
            if self._underline_opacity < 1.0:
                QTimer.singleShot(20, fade_tick)

        fade_tick()

    def set_active(self, step, animate=True):
        """Update tab styling and animate underline."""
        for i, label in enumerate(self.labels):
            step_num = i + 1
            is_active = step_num == step
            is_disabled = step_num in self.disabled_steps
            font = QFont()
            font.setPointSize(12)
            font.setBold(is_active)
            label.setFont(font)

            if is_disabled:
                label.setStyleSheet("color: #444444; background-color: transparent;")
            else:
                label.setStyleSheet(f"color: {'#e0e0e0' if is_active else '#777777'}; background-color: transparent;")

        self.active_step = step

        if animate:
            QTimer.singleShot(10, self._start_animation)
        else:
            QTimer.singleShot(10, self._set_initial_position)

    def _set_initial_position(self):
        """Set initial position after layout has settled."""
        label = self.labels[self.active_step - 1]
        label_rect = label.geometry()
        self._underline_x = label_rect.x()
        self._underline_width = label_rect.width()
        self.update()

    def _start_animation(self):
        """Start animation after layout has settled."""
        label = self.labels[self.active_step - 1]
        label_rect = label.geometry()
        target_x = label_rect.x()
        target_width = label_rect.width()
        source_width = self._underline_width

        self.anim = QPropertyAnimation(self, b"underline_x")
        self.anim.setDuration(180)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.anim.setStartValue(self._underline_x)
        self.anim.setEndValue(target_x)
        self.anim.valueChanged.connect(lambda: self._on_animation_value_changed(source_width, target_width))
        self.anim.finished.connect(lambda: self._on_animation_finished(target_width))
        self.anim.start()

    def _on_animation_value_changed(self, source_width, target_width):
        """Update width during animation based on progress."""
        if self.anim:
            progress = self.anim.currentTime() / self.anim.duration()
            self._underline_width = source_width + (target_width - source_width) * progress
            self.update()

    def _on_animation_finished(self, target_width):
        """Called when animation finishes."""
        self._underline_width = target_width
        self.update()

    @pyqtProperty(float)
    def underline_x(self):
        """Property for animated underline x position."""
        return self._underline_x

    @underline_x.setter
    def underline_x(self, value):
        """Set underline x position and trigger repaint."""
        self._underline_x = value
        self.update()

    def paintEvent(self, event):
        """Draw the underline."""
        painter = QPainter(self)

        if self._underline_width > 0:
            color = QColor("#00ff88")
            alpha = max(0, min(255, int(255 * self._underline_opacity)))
            color.setAlpha(alpha)
            underline_rect = QRect(
                int(self._underline_x),
                self.height() - 2,
                int(self._underline_width),
                2
            )
            painter.fillRect(underline_rect, color)

        painter.end()
