"""Settings widget for model and device selection."""
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import pyqtSignal


class SettingsWidget(QGroupBox):
    """Settings widget."""

    settings_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__("Settings")
        self.setStyleSheet("color: #00ff88;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # Model selector label
        model_label = QLabel("Transcription Model:")
        model_label.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(model_label)

        # Model radio buttons
        model_buttons_layout = QHBoxLayout()
        model_buttons_layout.setContentsMargins(0, 0, 0, 0)
        model_buttons_layout.setSpacing(12)

        self.model_buttons = {}
        button_style = """
            QPushButton {
                color: #777777;
                background-color: #2a2a2a;
                border: 1px solid #444444;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: normal;
                min-width: 65px;
                min-height: 24px;
            }
            QPushButton:hover {
                background-color: #333333;
                border: 1px solid #555555;
            }
            QPushButton:pressed {
                background-color: #1f1f1f;
            }
            QPushButton:checked {
                color: #1a1a1a;
                background-color: #00ff88;
                border: 1px solid #00ff88;
                font-weight: bold;
            }
        """
        for model in ["base", "small", "medium", "large"]:
            btn = QPushButton(model.capitalize())
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            self.model_buttons[model] = btn
            model_buttons_layout.addWidget(btn)

        model_buttons_layout.addStretch()
        layout.addLayout(model_buttons_layout)

        # Device selection label
        device_label = QLabel("Processing Mode:")
        device_label.setStyleSheet("color: #e0e0e0; background-color: transparent;")
        layout.addWidget(device_label)

        # Device checkboxes
        device_layout = QHBoxLayout()
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.setSpacing(12)

        self.device_buttons = {}
        for device in ["GPU", "CPU"]:
            btn = QPushButton(device)
            btn.setCheckable(True)
            btn.setStyleSheet(button_style)
            self.device_buttons[device] = btn
            device_layout.addWidget(btn)

        self.device_buttons["GPU"].setChecked(True)
        device_layout.addStretch()
        layout.addLayout(device_layout)

        layout.addStretch()
        self.setLayout(layout)

        # Connect signals after all widgets are created
        for btn in self.model_buttons.values():
            btn.clicked.connect(self._on_model_changed)
        for btn in self.device_buttons.values():
            btn.clicked.connect(self._on_device_changed)

        # Set defaults after signals are connected
        self.model_buttons["large"].setChecked(True)
        self.device_buttons["GPU"].setChecked(True)

    def _on_model_changed(self):
        """Handle model selection (mutually exclusive)."""
        sender = self.sender()
        if sender.isChecked():
            # Uncheck all other buttons
            for btn in self.model_buttons.values():
                if btn is not sender:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
        self._emit_settings()

    def _on_device_changed(self):
        """Handle device selection (mutually exclusive)."""
        sender = self.sender()
        if sender.isChecked():
            # Uncheck all other buttons
            for btn in self.device_buttons.values():
                if btn is not sender:
                    btn.blockSignals(True)
                    btn.setChecked(False)
                    btn.blockSignals(False)
        self._emit_settings()

    def _emit_settings(self):
        """Emit current settings."""
        selected_model = next((m for m, btn in self.model_buttons.items() if btn.isChecked()), "large")
        selected_device = next((d for d, btn in self.device_buttons.items() if btn.isChecked()), "GPU")
        settings = {
            "model": selected_model,
            "force_cpu": selected_device == "CPU"
        }
        self.settings_changed.emit(settings)

    def set_settings(self, model: str, force_cpu: bool):
        """Update UI to reflect settings (blocks signals to avoid recursion)."""
        for btn in self.model_buttons.values():
            btn.blockSignals(True)
        for btn in self.device_buttons.values():
            btn.blockSignals(True)

        self.model_buttons[model].setChecked(True)
        device = "CPU" if force_cpu else "GPU"
        self.device_buttons[device].setChecked(True)

        for btn in self.model_buttons.values():
            btn.blockSignals(False)
        for btn in self.device_buttons.values():
            btn.blockSignals(False)
