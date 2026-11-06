from pathlib import Path

from core.qt_compat import QtWidgets, QtGui, QThreadPool, QSize
from core.http_engine import HttpEngine
from ui.style import DARK_THEME_QSS
from ui.icons import Icons
from ui.components.collapsible_sidebar import CollapsibleSidebar
from ui.views.repeater_view import RepeaterView
from ui.views.automator_view import AutomatorView
from ui.views.history_view import HistoryView
from ui.views.settings_view import SettingsView


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rChipe - HTTP Analysis & POC Workbench")
        logo_path = Path(__file__).resolve().parents[1] / "assets" / "rChipe-logo.svg"
        self.setWindowIcon(QtGui.QIcon(str(logo_path)))

        self.setMinimumSize(600, 420)

        screen = QtGui.QGuiApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            win_w = min(1050, max(700, int(avail.width() * 0.86)))
            win_h = min(680, max(460, int(avail.height() * 0.84)))
            self.resize(win_w, win_h)
            win_x = avail.x() + (avail.width() - win_w) // 2
            win_y = avail.y() + (avail.height() - win_h) // 2
            self.move(win_x, win_y)
        else:
            self.resize(900, 600)

        self.setStyleSheet(DARK_THEME_QSS)

        self.http_engine = HttpEngine(verify_ssl=False, follow_redirects=False, timeout=15.0)
        self.thread_pool = QThreadPool()

        self._init_ui()
        self._setup_shortcuts()

    def _init_ui(self):
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.root_layout = QtWidgets.QHBoxLayout(self.central_widget)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.sidebar = CollapsibleSidebar(self)
        self.sidebar.mode_changed.connect(self._on_mode_changed)
        self.root_layout.addWidget(self.sidebar)

        self.content_container = QtWidgets.QWidget(self)
        self.content_layout = QtWidgets.QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        self.top_strip = QtWidgets.QWidget()
        self.top_strip.setObjectName("topBar")
        self.ts_layout = QtWidgets.QHBoxLayout(self.top_strip)
        self.ts_layout.setContentsMargins(6, 3, 6, 3)
        self.ts_layout.setSpacing(8)

        self.btn_toggle_sidebar = QtWidgets.QPushButton("  Sidebar")
        self.btn_toggle_sidebar.setIcon(Icons.get("sidebar", color="#969696", size=13))
        self.btn_toggle_sidebar.setIconSize(QSize(13, 13))
        self.btn_toggle_sidebar.setToolTip("Show / Hide Sidebar (Ctrl+B)")
        self.btn_toggle_sidebar.setFixedHeight(22)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar_visibility)
        self.ts_layout.addWidget(self.btn_toggle_sidebar)

        self.lbl_current_mode = QtWidgets.QLabel("Repeater")
        self.lbl_current_mode.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 11px;")
        self.ts_layout.addWidget(self.lbl_current_mode)

        self.ts_layout.addStretch()

        self.lbl_quick_hint = QtWidgets.QLabel("Ctrl+Enter: Send  |  Ctrl+B: Sidebar  |  Ctrl+1..4: Modes")
        self.lbl_quick_hint.setStyleSheet("color: #666666; font-size: 10px; font-family: monospace;")
        self.ts_layout.addWidget(self.lbl_quick_hint)

        self.content_layout.addWidget(self.top_strip)

        self.stack = QtWidgets.QStackedWidget(self)

        self.view_repeater = RepeaterView(self.http_engine, self.thread_pool)
        self.stack.addWidget(self.view_repeater)

        self.view_automator = AutomatorView(self.http_engine)
        self.stack.addWidget(self.view_automator)

        self.view_history = HistoryView()
        self.stack.addWidget(self.view_history)

        self.view_settings = SettingsView(self.http_engine)
        self.stack.addWidget(self.view_settings)

        self.content_layout.addWidget(self.stack, 1)
        self.root_layout.addWidget(self.content_container, 1)

        self.view_repeater.request_completed.connect(self.view_history.add_record)
        self.view_automator.request_completed.connect(self.view_history.add_record)
        self.view_history.send_to_repeater.connect(self._load_into_repeater)
        self.view_automator.send_to_repeater.connect(self._load_into_repeater)

    def _setup_shortcuts(self):
        sc_toggle = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+B"), self)
        sc_toggle.activated.connect(self._toggle_sidebar_visibility)

        sc_m0 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+1"), self)
        sc_m0.activated.connect(lambda: self.sidebar.set_active_mode(0))

        sc_m1 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+2"), self)
        sc_m1.activated.connect(lambda: self.sidebar.set_active_mode(1))

        sc_m2 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+3"), self)
        sc_m2.activated.connect(lambda: self.sidebar.set_active_mode(2))

        sc_m3 = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+4"), self)
        sc_m3.activated.connect(lambda: self.sidebar.set_active_mode(3))

    def _toggle_sidebar_visibility(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def _on_mode_changed(self, index: int):
        self.stack.setCurrentIndex(index)
        mode_titles = [
            "Repeater",
            "Automator",
            "History",
            "Settings",
        ]
        if 0 <= index < len(mode_titles):
            self.lbl_current_mode.setText(mode_titles[index])

    def _load_into_repeater(self, raw_text: str, target: str):
        self.view_repeater.load_raw_request(raw_text, target)
        self.sidebar.set_active_mode(0)
