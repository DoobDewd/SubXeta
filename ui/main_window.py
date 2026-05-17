from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QScrollArea, QGraphicsOpacityEffect
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve

from ui.styles import get_stylesheet
from ui.tab_bar import TabBar
from ui.steps.step1_transcribe import Step1Widget
from ui.steps.step2_review import Step2Widget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subtitle Comp App")
        self.setGeometry(100, 100, 1200, 800)

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
        layout.addWidget(self.step2)

        layout.addStretch()
        scroll_widget.setLayout(layout)
        scroll.setWidget(scroll_widget)
        return scroll

    def _on_transcription_started(self, file_path):
        self.step2.set_status("Remember: AI transcription can get some words wrong, make sure to review the subtitles!")
        self.tab_bar.enable_step(2, on_complete=lambda: self._show_step(2))
        # Placeholder data — will be replaced with real WhisperX output in Phase 3
        self.step2.populate_chunks([
            ("0:00.000", "Hello world"),
            ("0:02.500", "This is a test"),
        ])

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
