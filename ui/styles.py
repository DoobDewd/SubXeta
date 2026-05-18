"""Stylesheet for the Subtitle Comp App - dark alien theme."""


def get_stylesheet():
    return """
    QMainWindow {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }

    QWidget {
        background-color: #1a1a1a;
        color: #e0e0e0;
    }

    QGroupBox {
        border: 2px solid #00ff88;
        border-radius: 8px;
        margin-top: 12px;
        padding: 20px;
        color: #00ff88;
        font-weight: bold;
        font-size: 18px;
        background: rgba(0, 255, 136, 0.02);
    }

    QGroupBox:hover {
        border: 2px solid #00ffaa;
        background: rgba(0, 255, 136, 0.04);
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
    }

    QPushButton {
        background-color: #00ff88;
        color: #000000;
        border: 1px solid #00aa55;
        border-radius: 6px;
        padding: 12px 28px;
        font-weight: 600;
        font-size: 14px;
        margin: 5px 0px;
    }

    QPushButton:hover {
        background-color: #00ffaa;
        border: 2px solid #00ff88;
    }

    QPushButton:pressed {
        background-color: #00dd77;
        border: 2px solid #00aa55;
    }

    QPushButton:disabled {
        background-color: #333333;
        color: #666666;
    }

    QLineEdit {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #00ff88;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }

    QLineEdit:hover {
        background-color: #242424;
        border: 2px solid #00ff88;
    }

    QLineEdit:focus {
        background-color: #1f1f1f;
        border: 2px solid #00ffaa;
    }

    QComboBox {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #00ff88;
        border-radius: 3px;
        padding: 5px 5px 5px 8px;
        appearance: none;
    }

    QComboBox:hover {
        background-color: #242424;
        border: 2px solid #00ff88;
    }

    QComboBox:focus {
        background-color: #1f1f1f;
        border: 2px solid #00ffaa;
    }

    QComboBox::drop-down {
        border: none;
        background: none;
        width: 25px;
    }

    QComboBox::down-arrow {
        image: none;
    }

    QComboBox QAbstractItemView {
        background-color: #2a2a2a;
        color: #e0e0e0;
        selection-background-color: #00ff88;
        selection-color: #000000;
        border: 1px solid #00ff88;
        outline: none;
    }

    QSpinBox {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #00ff88;
        border-radius: 3px;
        padding: 5px;
    }

    QProgressBar {
        background-color: #2a2a2a;
        border: 1px solid #00ff88;
        border-radius: 3px;
        text-align: center;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: #00ff88;
        border-radius: 2px;
        margin: 0px;
    }

    QProgressBar::chunk[active="true"] {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop: 0 #00ff88,
                                    stop: 50 #00ffaa,
                                    stop: 100 #00ff88);
    }

    QLabel {
        color: #e0e0e0;
        font-size: 13px;
    }

    QTableWidget {
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #00ff88;
        border-radius: 6px;
        gridline-color: rgba(0, 255, 136, 0.2);
        margin: 5px 0px;
    }

    QTableWidget::item {
        padding: 8px;
        border: none;
    }

    QTableWidget::item:hover {
        background-color: rgba(0, 255, 136, 0.15);
    }

    QTableWidget::item:selected {
        background-color: rgba(0, 255, 136, 0.4);
        color: #00ff88;
    }

    QHeaderView::section {
        background-color: rgba(0, 255, 136, 0.1);
        color: #00ff88;
        padding: 8px;
        border: none;
        border-right: 1px solid rgba(0, 255, 136, 0.2);
        border-bottom: 1px solid rgba(0, 255, 136, 0.2);
        font-weight: 600;
    }

    QScrollBar:vertical {
        background-color: #2a2a2a;
        width: 12px;
        border: none;
    }

    QScrollBar::handle:vertical {
        background-color: #00ff88;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #00dd77;
    }

    QScrollArea {
        border: none;
        background: rgba(0, 255, 136, 0.02);
    }

    QFrame {
        border: none;
    }

    QTextEdit {
        background-color: #1a1a1a;
        color: #e0e0e0;
        border: 1px solid #00ff88;
        border-radius: 6px;
        padding: 12px;
        font-size: 13px;
        line-height: 1.5;
    }

    QTextEdit:hover {
        background-color: #242424;
        border: 2px solid #00ff88;
    }

    QTextEdit:focus {
        background-color: #1f1f1f;
        border: 2px solid #00ffaa;
    }
    """
