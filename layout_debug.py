#!/usr/bin/env python3
"""Debug layout - exact same layout as real app with highlighted containers."""
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea
from ui.tab_bar import TabBar
from ui.audio_player import AudioPlayerWidget
from ui.steps.step2_review import Step2Widget
from ui.styles import get_stylesheet

def add_debug_borders(widget):
    """Add red borders to widget and all children, with click handlers."""
    widget.setStyleSheet(widget.styleSheet() + "; border: 1px solid red;")

    def make_click_handler(w):
        def handler(event):
            name = w.objectName() or type(w).__name__
            size = f"{w.width()}x{w.height()}"
            layout = type(w.layout()).__name__ if w.layout() else "No layout"
            print(f"\nClicked: {name}")
            print(f"  Type: {type(w).__name__}")
            print(f"  Size: {size}")
            print(f"  Layout: {layout}")
            if w.layout():
                print(f"    Spacing: {w.layout().spacing()}")
                margins = w.layout().contentsMargins()
                print(f"    Margins: L={margins.left()} T={margins.top()} R={margins.right()} B={margins.bottom()}")
        return handler

    # Add click handlers
    widget.mousePressEvent = make_click_handler(widget)

    for child in widget.findChildren(QWidget):
        if child.parent():
            child.setStyleSheet(child.styleSheet() + "; border: 1px solid orange;")
            child.mousePressEvent = make_click_handler(child)

class LayoutDebug(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Layout Debug - Exact App Layout with Red Borders")
        self.setGeometry(100, 100, 1200, 1000)
        self.setFixedSize(1200, 1000)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)

        # Nav bar (like real app)
        nav_container = QWidget()
        nav_layout = QVBoxLayout()
        nav_layout.setContentsMargins(40, 12, 40, 0)
        nav_layout.setSpacing(0)
        tab_bar = TabBar()
        nav_layout.addWidget(tab_bar)
        nav_container.setLayout(nav_layout)
        nav_container.setStyleSheet("background-color: #1a1a1a; border: 3px solid red;")
        main_layout.addWidget(nav_container)

        # Content area (like real app)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 3px solid blue; }")

        scroll_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)

        # Audio player
        audio = AudioPlayerWidget()
        add_debug_borders(audio)
        layout.addWidget(audio)

        # Step 2
        step2 = Step2Widget()
        step2.populate_chunks([("0.000", "Test chunk 1"), ("2.500", "Test chunk 2")])
        add_debug_borders(step2)
        layout.addWidget(step2)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll_widget.setStyleSheet("border: 3px solid green;")
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)

        self.setStyleSheet(get_stylesheet())
        print("Red = borders added for debugging\nOrange = child widgets\n")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    debug = LayoutDebug()
    debug.show()
    sys.exit(app.exec())
