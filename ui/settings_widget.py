"""Settings widget for model, device, and template selection."""
from PyQt6.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import pyqtSignal
from core.subtitle_gen_alien import get_available_templates


class SettingsWidget(QGroupBox):
    """Settings widget."""

    settings_changed = pyqtSignal(dict)

    def __init__(self):
        super().__init__("Settings")
        self.setStyleSheet("color: #00ff88;")

        # Main horizontal layout for left (settings) and right (shortcuts) columns
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(40)

        # LEFT COLUMN - Settings
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        # Model selector label
        model_label = QLabel("Transcription Model:")
        model_label.setStyleSheet("color: #e0e0e0; background-color: transparent; font-weight: bold;")
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
        device_label.setStyleSheet("color: #e0e0e0; background-color: transparent; font-weight: bold;")
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

        # Template selection label
        template_label = QLabel("Subtitle Template:")
        template_label.setStyleSheet("color: #e0e0e0; background-color: transparent; font-weight: bold;")
        layout.addWidget(template_label)

        # Template buttons
        template_layout = QHBoxLayout()
        template_layout.setContentsMargins(0, 0, 0, 0)
        template_layout.setSpacing(12)

        self.template_buttons = {}
        available_templates = get_available_templates()

        # Display names for templates
        template_display_names = {
            "Zeta Reticuli Template.comp": "Zeta Reticuli",
            "Galactico Template.comp": "Galactico"
        }

        # Slightly wider style for template buttons
        template_button_style = button_style.replace("min-width: 65px;", "min-width: 85px;")

        for template in available_templates:
            display_name = template_display_names.get(template, template.replace(".comp", ""))
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            btn.setStyleSheet(template_button_style)
            self.template_buttons[template] = btn
            template_layout.addWidget(btn)

        template_layout.addStretch()
        layout.addLayout(template_layout)

        # FPS selection label
        fps_label = QLabel("Project Frame Rate:")
        fps_label.setStyleSheet("color: #e0e0e0; background-color: transparent; font-weight: bold;")
        layout.addWidget(fps_label)

        # FPS buttons
        fps_layout = QHBoxLayout()
        fps_layout.setContentsMargins(0, 0, 0, 0)
        fps_layout.setSpacing(12)

        self.fps_buttons = {}
        fps_values = [24, 30, 50, 60]

        fps_button_style = button_style.replace("min-width: 65px;", "min-width: 60px;")

        for fps in fps_values:
            fps_str = str(int(fps)) if fps == int(fps) else str(fps)
            btn = QPushButton(fps_str)
            btn.setCheckable(True)
            btn.setStyleSheet(fps_button_style)
            self.fps_buttons[fps] = btn
            fps_layout.addWidget(btn)

        self.fps_buttons[24].setChecked(True)
        fps_layout.addStretch()
        layout.addLayout(fps_layout)

        layout.addStretch()

        # Add left column (settings) to main layout
        settings_widget = QWidget()
        settings_widget.setStyleSheet("background-color: transparent;")
        settings_widget.setLayout(layout)
        main_layout.addWidget(settings_widget, 1)

        # RIGHT COLUMN - Keyboard Shortcuts
        shortcuts_layout = QVBoxLayout()
        shortcuts_layout.setContentsMargins(0, 0, 0, 0)
        shortcuts_layout.setSpacing(16)

        shortcuts_title = QLabel("Hotkeys:")
        shortcuts_title.setStyleSheet("color: #e0e0e0; background-color: transparent; font-weight: bold;")
        shortcuts_layout.addWidget(shortcuts_title)

        shortcuts = [
            ("Space", "Play/Pause"),
            ("←", "Scrub backward 25ms"),
            ("→", "Scrub forward 25ms"),
            ("↑", "Scrub forward 10ms"),
            ("↓", "Scrub backward 10ms"),
            ("I", "Set In point"),
            ("O", "Set Out point"),
            ("Right-click", "Set In/Out menu"),
        ]

        for key, action in shortcuts:
            shortcut_container = QHBoxLayout()
            shortcut_container.setContentsMargins(0, 0, 0, 0)
            shortcut_container.setSpacing(12)

            action_label = QLabel(action)
            action_label.setStyleSheet("color: #b0b0b0; background-color: transparent; font-size: 14px;")
            action_label.setWordWrap(True)
            shortcut_container.addWidget(action_label)

            key_label = QLabel(key)
            key_label.setStyleSheet("color: #00ff88; background-color: transparent; font-weight: bold; font-size: 14px; min-width: 65px;")
            shortcut_container.addWidget(key_label)

            shortcuts_layout.addLayout(shortcut_container)

        shortcuts_layout.addStretch()

        shortcuts_widget = QWidget()
        shortcuts_widget.setStyleSheet("background-color: transparent;")
        shortcuts_widget.setLayout(shortcuts_layout)
        main_layout.addWidget(shortcuts_widget, 1)

        self.setLayout(main_layout)

        # Connect signals after all widgets are created
        for btn in self.model_buttons.values():
            btn.clicked.connect(self._on_model_changed)
        for btn in self.device_buttons.values():
            btn.clicked.connect(self._on_device_changed)
        for btn in self.template_buttons.values():
            btn.clicked.connect(self._on_template_changed)
        for btn in self.fps_buttons.values():
            btn.clicked.connect(self._on_fps_changed)

    def _on_model_changed(self):
        """Handle model selection (mutually exclusive)."""
        sender = self.sender()
        if not sender.isChecked():
            # Prevent deselection - force it back to checked
            sender.blockSignals(True)
            sender.setChecked(True)
            sender.blockSignals(False)
            return

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
        if not sender.isChecked():
            # Prevent deselection - force it back to checked
            sender.blockSignals(True)
            sender.setChecked(True)
            sender.blockSignals(False)
            return

        # Uncheck all other buttons
        for btn in self.device_buttons.values():
            if btn is not sender:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        self._emit_settings()

    def _on_template_changed(self):
        """Handle template selection (mutually exclusive)."""
        sender = self.sender()
        if not sender.isChecked():
            # Prevent deselection - force it back to checked
            sender.blockSignals(True)
            sender.setChecked(True)
            sender.blockSignals(False)
            return

        # Uncheck all other buttons
        for btn in self.template_buttons.values():
            if btn is not sender:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        self._emit_settings()

    def _on_fps_changed(self):
        """Handle FPS selection (mutually exclusive)."""
        sender = self.sender()
        if not sender.isChecked():
            # Prevent deselection - force it back to checked
            sender.blockSignals(True)
            sender.setChecked(True)
            sender.blockSignals(False)
            return

        # Uncheck all other buttons
        for btn in self.fps_buttons.values():
            if btn is not sender:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)
        self._emit_settings()

    def _emit_settings(self):
        """Emit current settings."""
        selected_model = next((m for m, btn in self.model_buttons.items() if btn.isChecked()), "large")
        selected_device = next((d for d, btn in self.device_buttons.items() if btn.isChecked()), "GPU")
        selected_template = next((t for t, btn in self.template_buttons.items() if btn.isChecked()), "Zeta Reticuli Template.comp")
        selected_fps = next((f for f, btn in self.fps_buttons.items() if btn.isChecked()), 24)
        settings = {
            "model": selected_model,
            "force_cpu": selected_device == "CPU",
            "template": selected_template,
            "fps": selected_fps
        }
        self.settings_changed.emit(settings)

    def set_settings(self, model: str, force_cpu: bool, template: str = "Zeta Reticuli Template.comp", fps: float = 24):
        """Update UI to reflect settings (blocks signals to avoid recursion)."""
        for btn in self.model_buttons.values():
            btn.blockSignals(True)
        for btn in self.device_buttons.values():
            btn.blockSignals(True)
        for btn in self.template_buttons.values():
            btn.blockSignals(True)
        for btn in self.fps_buttons.values():
            btn.blockSignals(True)

        # Uncheck all buttons before checking the selected one
        for btn in self.model_buttons.values():
            btn.setChecked(False)
        for btn in self.device_buttons.values():
            btn.setChecked(False)
        for btn in self.template_buttons.values():
            btn.setChecked(False)
        for btn in self.fps_buttons.values():
            btn.setChecked(False)

        # Check the selected buttons
        self.model_buttons[model].setChecked(True)
        device = "CPU" if force_cpu else "GPU"
        self.device_buttons[device].setChecked(True)
        if template in self.template_buttons:
            self.template_buttons[template].setChecked(True)
        elif "Zeta Reticuli Template.comp" in self.template_buttons:
            self.template_buttons["Zeta Reticuli Template.comp"].setChecked(True)
        if fps in self.fps_buttons:
            self.fps_buttons[fps].setChecked(True)
        else:
            self.fps_buttons[24].setChecked(True)

        for btn in self.model_buttons.values():
            btn.blockSignals(False)
        for btn in self.device_buttons.values():
            btn.blockSignals(False)
        for btn in self.template_buttons.values():
            btn.blockSignals(False)
        for btn in self.fps_buttons.values():
            btn.blockSignals(False)
