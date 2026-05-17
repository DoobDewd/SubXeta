"""Custom tab bar with sliding underline indicator."""
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, QTimer, pyqtSignal, pyqtProperty
from PyQt6.QtGui import QFont, QPainter, QColor


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

        for i, text in enumerate(["Transcribe Audio", "Review & Generate"]):
            label = QLabel(text)
            label.setCursor(Qt.CursorShape.PointingHandCursor)
            label.setContentsMargins(0, 0, 0, 0)
            label.setMaximumHeight(28)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            label.step = i + 1
            label.mousePressEvent = lambda e, s=i+1: self.on_tab_click(s)
            self.labels.append(label)
            layout.addWidget(label)

        layout.addStretch()
        self.setLayout(layout)

    def showEvent(self, event):
        """Initialize underline position when shown."""
        super().showEvent(event)
        self.set_active(1, animate=False)

    def on_tab_click(self, step):
        self.set_active(step, animate=True)
        self.tab_changed.emit(step)

    def set_active(self, step, animate=True):
        """Update tab styling and animate underline."""
        for i, label in enumerate(self.labels):
            is_active = (i + 1) == step
            font = QFont()
            font.setPointSize(12)
            font.setBold(is_active)
            label.setFont(font)
            label.setStyleSheet(f"color: {'#e0e0e0' if is_active else '#777777'}; background-color: transparent;")

        self.active_step = step

        if animate:
            # Defer animation until layout has settled
            QTimer.singleShot(10, lambda: self._start_animation())
        else:
            # Defer initial positioning until layout settles
            QTimer.singleShot(10, lambda: self._set_initial_position())

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
            underline_rect = QRect(
                int(self._underline_x),
                self.height() - 2,
                int(self._underline_width),
                2
            )
            painter.fillRect(underline_rect, QColor("#00ff88"))

        painter.end()
