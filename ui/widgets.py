"""Custom widgets for the Subtitle Comp App."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter
from ui.animations import CRTAnimatedMixin
from ui import theme


class DragDropArea(QWidget, CRTAnimatedMixin):
    fileSelected = pyqtSignal(str)

    def __init__(self, placeholder_text="Drag files here"):
        super().__init__()
        self.file_path = None
        self.placeholder_text = placeholder_text
        self._is_hovering = False
        self._file_imported = False
        self._init_crt_effect()

        layout = QVBoxLayout()
        self.label = QLabel(placeholder_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setStyleSheet(self._STYLE_DEFAULT)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setMinimumHeight(140)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    _STYLE_DEFAULT  = f"QLabel {{ border: 2px dashed {theme.GREEN}; border-radius: 5px; padding: 40px; color: {theme.GREEN}; background-color: transparent; }}"
    _STYLE_HOVER    = f"QLabel {{ border: 2px solid {theme.GREEN};  border-radius: 5px; padding: 40px; color: {theme.GREEN}; background-color: transparent; }}"
    _STYLE_DRAGGING = f"QLabel {{ border: 2px dashed {theme.MAGENTA}; border-radius: 5px; padding: 40px; color: {theme.MAGENTA}; background-color: transparent; }}"

    def _tick_crt_effect(self):
        self._crt_effect.tick()
        if self._is_hovering or self._file_imported:
            self.update()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet(self._STYLE_DRAGGING)

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet(self._STYLE_DEFAULT)

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_path = files[0]
            self.setText(self.file_path)
            self._file_imported = True
            self._crt_effect.start_sweep()
            self.update()
            self.fileSelected.emit(self.file_path)
        self.label.setStyleSheet(self._STYLE_DEFAULT)

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.file_path or ""

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.setStyleSheet(self._STYLE_HOVER)
        self._is_hovering = True
        self._crt_effect.start_sweep()

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.label.setStyleSheet(self._STYLE_DEFAULT)
        self._is_hovering = False

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select audio or video file",
            "",
            "Audio/Video Files (*.mp3 *.wav *.m4a *.mp4 *.mov *.avi);;All Files (*)"
        )
        if file_path:
            self.file_path = file_path
            self.setText(file_path)
            self._file_imported = True
            self._crt_effect.start_sweep()
            self.update()
            self.fileSelected.emit(file_path)

    def paintEvent(self, event):
        super().paintEvent(event)

        if self._is_hovering or self._file_imported:
            painter = QPainter(self)
            label_rect = self.label.geometry()
            self._draw_crt_effect(painter, label_rect)
            painter.end()
