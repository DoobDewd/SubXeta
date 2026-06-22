"""Stylesheet for the Subtitle Comp App - dark alien theme."""
from string import Template

from ui import theme


_STYLESHEET = Template("""
    QMainWindow {
        background-color: $BG;
        color: $TEXT;
    }

    QWidget {
        background-color: $BG;
        color: $TEXT;
    }

    QGroupBox {
        border: 2px solid $GREEN;
        border-radius: 8px;
        margin-top: 12px;
        padding: 20px;
        color: $GREEN;
        font-weight: bold;
        font-size: 18px;
        background: ${GREEN_A02};
    }

    QGroupBox:hover {
        border: 2px solid $GREEN_BRIGHT;
        background: ${GREEN_A04};
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 8px 0 8px;
    }

    QPushButton {
        background-color: $GREEN;
        color: $BLACK;
        border: 2px solid $GREEN_BORDER;
        border-radius: 6px;
        padding: 10px 28px;
        font-weight: 600;
        font-size: 14px;
        margin: 5px 0px;
        text-align: center;
    }

    QPushButton:hover {
        background-color: $GREEN_BRIGHT;
        border: 2px solid $GREEN;
    }

    QPushButton:pressed {
        background-color: $GREEN_PRESSED;
        border: 2px solid $GREEN_BORDER;
    }

    QPushButton:disabled {
        background-color: $DISABLED_BG;
        color: $TEXT_DISABLED;
    }

    QLineEdit {
        background-color: $SURFACE;
        color: $TEXT;
        border: 1px solid $GREEN;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 13px;
    }

    QLineEdit:hover {
        background-color: $BG_HOVER;
        border: 2px solid $GREEN;
    }

    QLineEdit:focus {
        background-color: $BG_FOCUS;
        border: 2px solid $GREEN_BRIGHT;
    }

    QComboBox {
        background-color: $SURFACE;
        color: $TEXT;
        border: 1px solid $GREEN;
        border-radius: 3px;
        padding: 5px 5px 5px 8px;
    }

    QComboBox:hover {
        background-color: $BG_HOVER;
        border: 2px solid $GREEN;
    }

    QComboBox:focus {
        background-color: $BG_FOCUS;
        border: 2px solid $GREEN_BRIGHT;
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
        background-color: $SURFACE;
        color: $TEXT;
        selection-background-color: $GREEN;
        selection-color: $BLACK;
        border: 1px solid $GREEN;
        outline: none;
    }

    QSpinBox {
        background-color: $SURFACE;
        color: $TEXT;
        border: 1px solid $GREEN;
        border-radius: 3px;
        padding: 5px;
    }

    QProgressBar {
        background-color: $SURFACE;
        border: 1px solid $GREEN;
        border-radius: 3px;
        color: transparent;
        height: 20px;
    }

    QProgressBar::chunk {
        background-color: $GREEN;
        border-radius: 2px;
        margin: 0px;
    }

    QProgressBar::chunk[active="true"] {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                    stop: 0 $GREEN,
                                    stop: 50 $GREEN_BRIGHT,
                                    stop: 100 $GREEN);
    }

    QLabel {
        color: $TEXT;
        font-size: 13px;
    }

    QTableWidget {
        background-color: $BG;
        color: $TEXT;
        border: 1px solid $GREEN;
        border-radius: 6px;
        gridline-color: ${GREEN_A20};
        margin: 5px 0px;
    }

    QTableWidget::item {
        padding: 8px;
        border: none;
    }

    QTableWidget::item:hover {
        background-color: ${GREEN_A15};
    }

    QTableWidget::item:selected {
        background-color: ${GREEN_A40};
        color: $GREEN;
    }

    QHeaderView::section {
        background-color: ${GREEN_A10};
        color: $GREEN;
        padding: 8px;
        border: none;
        border-right: 1px solid ${GREEN_A20};
        border-bottom: 1px solid ${GREEN_A20};
        font-weight: 600;
    }

    QScrollBar:vertical {
        background-color: $SURFACE;
        width: 12px;
        border: none;
    }

    QScrollBar::handle:vertical {
        background-color: $GREEN;
        border-radius: 6px;
        min-height: 20px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: $GREEN_PRESSED;
    }

    QScrollArea {
        border: none;
        background: ${GREEN_A02};
    }

    QFrame {
        border: none;
    }

    QTextEdit {
        background-color: $BG;
        color: $TEXT;
        border: 1px solid $GREEN;
        border-radius: 6px;
        padding: 12px;
        font-size: 13px;
        line-height: 1.5;
    }

    QTextEdit:hover {
        background-color: $BG_HOVER;
        border: 2px solid $GREEN;
    }

    QTextEdit:focus {
        background-color: $BG_FOCUS;
        border: 2px solid $GREEN_BRIGHT;
    }
    """)


def get_stylesheet():
    subs = theme.stylesheet_vars()
    # Pre-rendered green-with-alpha values used throughout the sheet
    subs.update({
        "GREEN_A02": theme.green_rgba(0.02),
        "GREEN_A04": theme.green_rgba(0.04),
        "GREEN_A10": theme.green_rgba(0.1),
        "GREEN_A15": theme.green_rgba(0.15),
        "GREEN_A20": theme.green_rgba(0.2),
        "GREEN_A40": theme.green_rgba(0.4),
    })
    return _STYLESHEET.substitute(subs)
