"""Reusable animation utilities."""
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter, QColor
import random

from ui import theme


class CRTEffect:
    """Reusable CRT scanline animation effect."""

    def __init__(self):
        self._scan_offset = 0.0
        self._frame = 0
        self._sweep_active = False
        self._sweep_progress = 0.0
        self._frames_until_next_sweep = 0

    def tick(self):
        """Update animation state."""
        self._scan_offset += 0.08
        self._frame += 1
        if self._scan_offset >= 2.0:
            self._scan_offset -= 2.0

        if self._sweep_active:
            self._sweep_progress += 0.08
            if self._sweep_progress >= 1.0:
                self._sweep_active = False
                self._frames_until_next_sweep = random.randint(40, 120)
        else:
            self._frames_until_next_sweep -= 1
            if self._frames_until_next_sweep <= 0:
                self._sweep_active = True
                self._sweep_progress = 0.0

    def draw(self, painter, rect):
        """Draw the CRT effect (scanlines + sweep animation)."""
        h = rect.height()
        w = rect.width()
        freq = 6.5

        # Scanlines
        flicker_val = (self._frame % 2) / 1.0
        if flicker_val > 1.0:
            flicker_val = 2.0 - flicker_val

        for y in range(h):
            frac_val = (y * freq + self._scan_offset) % 1.0
            scanline_val = abs(frac_val - 0.5) * 2.0
            alpha = int(scanline_val * 35)
            alpha = int(alpha * (0.85 + flicker_val * 0.15))

            color = QColor(*theme.GREEN_RGB, alpha)
            painter.setPen(color)
            painter.drawLine(rect.x(), rect.y() + y, rect.x() + w, rect.y() + y)

        # Sweep line (only when active)
        if self._sweep_active:
            sweep_y = int(self._sweep_progress * h)
            if 0 <= sweep_y < h:
                sweep_color = QColor(*theme.GREEN_RGB, 120)
                painter.setPen(sweep_color)
                painter.drawLine(rect.x(), rect.y() + sweep_y, rect.x() + w, rect.y() + sweep_y)

    def start_sweep(self):
        """Start a sweep animation."""
        self._sweep_active = True
        self._sweep_progress = 0.0


class CRTAnimatedMixin:
    """Mixin to add CRT scanline animation to any widget."""

    def _init_crt_effect(self):
        """Initialize CRT effect. Must call this in __init__."""
        self._crt_effect = CRTEffect()
        self._crt_timer = QTimer(self)
        self._crt_timer.setInterval(50)
        self._crt_timer.timeout.connect(self._tick_crt_effect)
        self._crt_timer.start()

    def _tick_crt_effect(self):
        """Update CRT effect (override for custom behavior)."""
        self._crt_effect.tick()
        self.update()

    def _draw_crt_effect(self, painter, rect):
        """Draw CRT effect on painter. Call from paintEvent."""
        self._crt_effect.draw(painter, rect)


class TypingAnimator:
    """Handles character-by-character typing animation for any widget with setText()."""

    def __init__(self, char_delay_ms=25):
        self.char_delay_ms = char_delay_ms
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._targets = []
        self._current_index = 0
        self._char_index = 0

    def animate_sequence(self, targets):
        """Animate a sequence of widgets typing text.

        Args:
            targets: list of (widget, text) or (widget, text, on_done) tuples.
                    on_done callback is invoked when that widget finishes typing.
        """
        self._targets = []
        for item in targets:
            if len(item) == 2:
                widget, text = item
                self._targets.append((widget, text, None))
            else:
                widget, text, on_done = item
                self._targets.append((widget, text, on_done))

        self._current_index = 0
        self._char_index = 0
        self._timer.setInterval(self.char_delay_ms)
        self._timer.start()

    def animate_single(self, widget, text, on_done=None):
        """Animate text typing into a single widget."""
        self.animate_sequence([(widget, text, on_done)])

    def restart(self):
        """Restart animation from the beginning."""
        if not self._targets:
            return
        if self._timer.isActive():
            self._timer.stop()
        for widget, _, _ in self._targets:
            widget.setText("")
        self._current_index = 0
        self._char_index = 0
        self._timer.start()

    def stop(self):
        """Stop the animation."""
        self._timer.stop()

    def is_active(self):
        """True while a typing animation is currently in progress."""
        return self._timer.isActive()

    def _tick(self):
        """Internal timer tick."""
        if self._current_index >= len(self._targets):
            self._timer.stop()
            return

        widget, full_text, on_done = self._targets[self._current_index]

        if self._char_index < len(full_text):
            widget.setText(full_text[: self._char_index + 1])
            self._char_index += 1
        else:
            if on_done:
                on_done()
            self._current_index += 1
            self._char_index = 0
