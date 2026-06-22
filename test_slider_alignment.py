"""Test script to measure slider handle vs calculated line offset."""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor
from ui.audio_player import CustomSlider

class AlignmentTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Slider Alignment Test - Adjust offset with arrow keys")
        self.setGeometry(100, 100, 800, 300)
        self.offset = 0  # Offset to test

        widget = QWidget()
        layout = QVBoxLayout()

        # Test slider
        self.slider = CustomSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(10000)
        self.slider.setValue(0)
        layout.addWidget(self.slider)

        # Info label
        self.info_label = QLabel("Use UP/DOWN arrows to adjust offset. LEFT/RIGHT to move slider.")
        layout.addWidget(self.info_label)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connect to track position
        self.slider.valueChanged.connect(self._on_value_changed)

        # Draw overlay
        self.slider.paintEvent = self._test_paint

        self.setFocus()

    def _test_paint(self, event):
        """Custom paint to show handle vs calculated position."""
        # Call original paint
        from PyQt6.QtWidgets import QSlider
        QSlider.paintEvent(self.slider, event)

        # Draw debug info
        painter = QPainter(self.slider)

        value = self.slider.value()
        max_val = self.slider.maximum()

        # Get calculated position with offset
        calc_x = self.slider._value_to_pixel(value) + self.offset

        # Draw red line at calculated position
        painter.setPen(QColor(255, 0, 0))
        painter.drawLine(int(calc_x), 0, int(calc_x), self.slider.height())

        # Draw text showing position
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(10, 30, f"Value: {value}/{max_val} | Offset: {self.offset}")
        painter.drawText(10, 50, f"Line X: {calc_x:.1f}")

        painter.end()

    def _on_value_changed(self, value):
        """Update info when slider moves."""
        calc_x = self.slider._value_to_pixel(value) + self.offset
        max_val = self.slider.maximum()
        self.info_label.setText(
            f"Value: {value}/{max_val} | "
            f"Line X: {calc_x:.1f} | "
            f"Offset: {self.offset}px | "
            f"Slider Width: {self.slider.width()}"
        )

    def keyPressEvent(self, event):
        """Handle arrow keys to adjust offset."""
        step = 1 if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else 0.1
        if event.key() == Qt.Key.Key_Up:
            self.offset += step
            self.slider.update()
        elif event.key() == Qt.Key.Key_Down:
            self.offset -= step
            self.slider.update()
        elif event.key() == Qt.Key.Key_Left:
            self.slider.setValue(max(0, self.slider.value() - 100))
        elif event.key() == Qt.Key.Key_Right:
            self.slider.setValue(min(self.slider.maximum(), self.slider.value() + 100))
        self._on_value_changed(self.slider.value())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AlignmentTestWindow()
    window.show()
    sys.exit(app.exec())
