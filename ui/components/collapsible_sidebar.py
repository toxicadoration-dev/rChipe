from pathlib import Path

from core.qt_compat import QtWidgets, QtCore, QtGui, Signal, QSize
from ui.icons import Icons


class CollapsibleSidebar(QtWidgets.QWidget):
    mode_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.is_collapsed = False
        self.current_index = 0

        self.full_width = 125
        self.collapsed_width = 40

        self._init_ui()

    def _init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1)

        self.header_widget = QtWidgets.QWidget()
        self.header_widget.setStyleSheet("background-color: #252526; border-bottom: 1px solid #333337;")
        self.header_layout = QtWidgets.QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(8, 5, 5, 5)

        self.logo_label = QtWidgets.QLabel()
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "rChipe-logo.svg"
        logo = QtGui.QPixmap(str(logo_path))
        logo = logo.scaled(26, 26, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)
        self.logo_label.setPixmap(logo)
        self.header_layout.addWidget(self.logo_label)

        self.btn_toggle = QtWidgets.QPushButton()
        self.btn_toggle.setIcon(Icons.get("chevron_left", color="#969696", size=14))
        self.btn_toggle.setIconSize(QSize(14, 14))
        self.btn_toggle.setFixedSize(22, 22)
        self.btn_toggle.setToolTip("Toggle sidebar width")
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background: #2d2d30;
                border: 1px solid #3e3e42;
                border-radius: 2px;
                padding: 0px;
            }
            QPushButton:hover {
                background: #3e3e42;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_collapse)
        self.header_layout.addWidget(self.btn_toggle)

        self.layout.addWidget(self.header_widget)

        self.btn_group = QtWidgets.QButtonGroup(self)
        self.btn_group.setExclusive(True)

        self.modes = [
            ("repeater", "Repeater", "Manual HTTP request craft and replay"),
            ("automator", "Automator", "Parameterized batch execution"),
            ("history", "History", "Session request/response log"),
            ("settings", "Settings", "Network, upstream proxy, and SSL parameters"),
        ]

        self.buttons = []
        for i, (icon_name, full_text, tooltip) in enumerate(self.modes):
            btn = QtWidgets.QPushButton()
            btn.setIcon(Icons.get(icon_name, color="#969696", size=14))
            btn.setIconSize(QSize(14, 14))
            btn.setText(f"  {full_text}")
            btn.setCheckable(True)
            btn.setToolTip(tooltip)
            btn.setProperty("icon_name", icon_name)
            btn.setProperty("full_text", full_text)
            btn.clicked.connect(lambda checked, idx=i: self._on_button_clicked(idx))
            self.btn_group.addButton(btn, i)
            self.buttons.append(btn)
            self.layout.addWidget(btn)

        self.buttons[0].setChecked(True)

        self.layout.addStretch()

        self.footer_label = QtWidgets.QLabel("Ctrl+Enter: Send\nCtrl+B: Sidebar")
        self.footer_label.setStyleSheet("color: #666666; font-size: 9px; padding: 6px 8px; font-family: monospace;")
        self.layout.addWidget(self.footer_label)

        self.setFixedWidth(self.full_width)

    def _on_button_clicked(self, index: int):
        self.current_index = index
        self.mode_changed.emit(index)

    def set_active_mode(self, index: int):
        if 0 <= index < len(self.buttons):
            self.buttons[index].setChecked(True)
            self.current_index = index
            self.mode_changed.emit(index)

    def toggle_collapse(self):
        self.set_collapsed(not self.is_collapsed)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        if self.is_collapsed:
            self.setFixedWidth(self.collapsed_width)
            self.logo_label.setVisible(False)
            self.footer_label.setVisible(False)
            self.btn_toggle.setIcon(Icons.get("chevron_right", color="#969696", size=14))
            for btn in self.buttons:
                btn.setText("")
                btn.setStyleSheet("text-align: center; padding: 8px 0px;")
        else:
            self.setFixedWidth(self.full_width)
            self.logo_label.setVisible(True)
            self.footer_label.setVisible(True)
            self.btn_toggle.setIcon(Icons.get("chevron_left", color="#969696", size=14))
            for btn in self.buttons:
                btn.setText(f"  {btn.property('full_text')}")
                btn.setStyleSheet("""
                    text-align: left;
                    padding: 6px 10px;
                    font-size: 11px;
                """)
