from core.qt_compat import QtWidgets, Qt, QSize, Signal
from core.http_engine import HttpEngine
from ui.icons import Icons


class SettingsView(QtWidgets.QWidget):
    settings_updated = Signal()

    def __init__(self, http_engine: HttpEngine, parent=None):
        super().__init__(parent)
        self.http_engine = http_engine
        self._init_ui()

    def _init_ui(self):
        self.root_layout = QtWidgets.QVBoxLayout(self)
        self.root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll = QtWidgets.QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.container = QtWidgets.QWidget()
        self.layout = QtWidgets.QVBoxLayout(self.container)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        self.lbl_title = QtWidgets.QLabel("NETWORK & PROXY CONFIGURATION")
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #cccccc; letter-spacing: 0.5px;")
        self.layout.addWidget(self.lbl_title)

        self.group_net = QtWidgets.QGroupBox("Protocol & TLS Parameters")
        self.g_layout = QtWidgets.QVBoxLayout(self.group_net)
        self.g_layout.setSpacing(8)

        self.chk_ssl = QtWidgets.QCheckBox("Verify TLS/SSL certificates (uncheck for self-signed lab targets)")
        self.chk_ssl.setChecked(self.http_engine.verify_ssl)
        self.g_layout.addWidget(self.chk_ssl)

        self.chk_redirects = QtWidgets.QCheckBox("Follow HTTP redirects (301, 302, 307)")
        self.chk_redirects.setChecked(self.http_engine.follow_redirects)
        self.g_layout.addWidget(self.chk_redirects)

        self.timeout_layout = QtWidgets.QHBoxLayout()
        self.lbl_timeout = QtWidgets.QLabel("Request timeout (seconds):")
        self.lbl_timeout.setStyleSheet("color: #858585;")
        self.timeout_layout.addWidget(self.lbl_timeout)

        self.spin_timeout = QtWidgets.QDoubleSpinBox()
        self.spin_timeout.setRange(1.0, 120.0)
        self.spin_timeout.setValue(self.http_engine.timeout)
        self.spin_timeout.setFixedWidth(70)
        self.timeout_layout.addWidget(self.spin_timeout)
        self.timeout_layout.addStretch()
        self.g_layout.addLayout(self.timeout_layout)

        self.layout.addWidget(self.group_net)

        self.group_proxy = QtWidgets.QGroupBox("Upstream Proxy Chaining")
        self.p_layout = QtWidgets.QVBoxLayout(self.group_proxy)
        self.p_layout.setSpacing(8)

        self.chk_proxy_enable = QtWidgets.QCheckBox("Enable upstream proxy (e.g. forward to Burp Suite / ZAP at 127.0.0.1:8080)")
        self.chk_proxy_enable.setChecked(bool(self.http_engine.proxy))
        self.p_layout.addWidget(self.chk_proxy_enable)

        self.proxy_input_layout = QtWidgets.QHBoxLayout()
        self.lbl_proxy = QtWidgets.QLabel("Proxy URL:")
        self.lbl_proxy.setStyleSheet("color: #858585;")
        self.proxy_input_layout.addWidget(self.lbl_proxy)

        self.txt_proxy = QtWidgets.QLineEdit()
        self.txt_proxy.setPlaceholderText("http://127.0.0.1:8080")
        self.txt_proxy.setText(self.http_engine.proxy or "http://127.0.0.1:8080")
        self.proxy_input_layout.addWidget(self.txt_proxy)
        self.p_layout.addLayout(self.proxy_input_layout)

        self.layout.addWidget(self.group_proxy)

        self.btn_save = QtWidgets.QPushButton("  Save Settings")
        self.btn_save.setObjectName("btnAccent")
        self.btn_save.setIcon(Icons.get("settings", color="#ffffff", size=12))
        self.btn_save.setIconSize(QSize(12, 12))
        self.btn_save.setFixedWidth(140)
        self.btn_save.clicked.connect(self.save_settings)
        self.layout.addWidget(self.btn_save)

        self.layout.addStretch()

        self.scroll.setWidget(self.container)
        self.root_layout.addWidget(self.scroll)

    def save_settings(self):
        self.http_engine.verify_ssl = self.chk_ssl.isChecked()
        self.http_engine.follow_redirects = self.chk_redirects.isChecked()
        self.http_engine.timeout = self.spin_timeout.value()

        if self.chk_proxy_enable.isChecked() and self.txt_proxy.text().strip():
            self.http_engine.proxy = self.txt_proxy.text().strip()
        else:
            self.http_engine.proxy = None

        QtWidgets.QMessageBox.information(
            self, "Configuration Saved", "Network parameters updated successfully."
        )
        self.settings_updated.emit()
