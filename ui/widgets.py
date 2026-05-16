"""Custom widgets for the Subtitle Comp App."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QCursor


class DragDropArea(QWidget):
    fileSelected = pyqtSignal(str)

    def __init__(self, placeholder_text="Drag files here"):
        super().__init__()
        self.file_path = None
        self.placeholder_text = placeholder_text

        layout = QVBoxLayout()
        self.label = QLabel(placeholder_text)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(10)
        self.label.setFont(font)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                cursor: pointer;
            }
        """)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setAcceptDrops(True)
        self.setMinimumHeight(140)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #ff00ff;
                    border-radius: 5px;
                    padding: 40px;
                    color: #ff00ff;
                }
            """)

    def dragLeaveEvent(self, event):
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
            }
        """)

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_path = files[0]
            self.setText(self.file_path)
            self.fileSelected.emit(self.file_path)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
            }
        """)

    def setText(self, text):
        self.label.setText(text)

    def text(self):
        return self.file_path or ""

    def enterEvent(self, event):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px solid #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                cursor: pointer;
                background-color: rgba(0, 255, 136, 0.1);
            }
        """)

    def leaveEvent(self, event):
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #00ff88;
                border-radius: 5px;
                padding: 40px;
                color: #00ff88;
                cursor: pointer;
            }
        """)

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
            self.fileSelected.emit(file_path)
