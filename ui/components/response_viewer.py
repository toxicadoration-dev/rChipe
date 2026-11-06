import json
from core.qt_compat import QtWidgets, QtGui, Qt, QSize
from core.models import ResponseModel
from ui.icons import Icons
from ui.components.code_editor import HttpCodeEditor, JsonSyntaxHighlighter


class ResponseViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_response: ResponseModel = None
        self._init_ui()

    def _init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

        self.meta_bar = QtWidgets.QHBoxLayout()
        self.meta_bar.setContentsMargins(0, 0, 0, 2)
        self.meta_bar.setSpacing(6)

        self.lbl_title = QtWidgets.QLabel("RESPONSE")
        self.lbl_title.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.meta_bar.addWidget(self.lbl_title)

        self.badge_status = QtWidgets.QLabel("READY")
        self.badge_status.setObjectName("badgeStatus")
        self.badge_status.setStyleSheet("""
            background: #252526;
            color: #858585;
            border: 1px solid #3e3e42;
            padding: 1px 6px;
            font-family: monospace;
            font-size: 10px;
        """)
        self.meta_bar.addWidget(self.badge_status)

        self.lbl_time = QtWidgets.QLabel("0 ms")
        self.lbl_time.setStyleSheet("color: #858585; font-size: 10px; font-family: monospace;")
        self.meta_bar.addWidget(self.lbl_time)

        self.lbl_size = QtWidgets.QLabel("0 B")
        self.lbl_size.setStyleSheet("color: #858585; font-size: 10px; font-family: monospace;")
        self.meta_bar.addWidget(self.lbl_size)

        self.meta_bar.addStretch()

        self.btn_copy = QtWidgets.QPushButton("  Copy Raw")
        self.btn_copy.setIcon(Icons.get("copy", color="#969696", size=12))
        self.btn_copy.setIconSize(QSize(12, 12))
        self.btn_copy.setToolTip("Copy complete raw HTTP response")
        self.btn_copy.clicked.connect(self._copy_raw)
        self.meta_bar.addWidget(self.btn_copy)

        self.layout.addLayout(self.meta_bar)

        self.tab_widget = QtWidgets.QTabWidget()

        self.editor_raw = HttpCodeEditor(read_only=True)
        self.tab_widget.addTab(self.editor_raw, "Raw HTTP")

        self.editor_pretty = HttpCodeEditor(read_only=True)
        self.pretty_highlighter = JsonSyntaxHighlighter(self.editor_pretty.document())
        self.tab_widget.addTab(self.editor_pretty, "Pretty Body")

        self.headers_table = QtWidgets.QTableWidget()
        self.headers_table.setColumnCount(2)
        self.headers_table.setHorizontalHeaderLabels(["HEADER", "VALUE"])
        self.headers_table.horizontalHeader().setStretchLastSection(True)
        self.headers_table.horizontalHeader().setDefaultSectionSize(140)
        self.headers_table.verticalHeader().setVisible(False)
        self.tab_widget.addTab(self.headers_table, "Headers")

        self.layout.addWidget(self.tab_widget)

        self.search_layout = QtWidgets.QHBoxLayout()
        self.search_layout.setContentsMargins(0, 1, 0, 0)
        self.search_layout.setSpacing(4)

        self.lbl_find = QtWidgets.QLabel("FIND:")
        self.lbl_find.setStyleSheet("color: #666666; font-size: 10px; font-weight: 600;")
        self.search_layout.addWidget(self.lbl_find)

        self.txt_search = QtWidgets.QLineEdit()
        self.txt_search.setPlaceholderText("Filter response body...")
        self.txt_search.textChanged.connect(self._search_text)
        self.search_layout.addWidget(self.txt_search, 1)

        self.btn_find_next = QtWidgets.QPushButton("  Next")
        self.btn_find_next.setIcon(Icons.get("search", color="#969696", size=11))
        self.btn_find_next.setIconSize(QSize(11, 11))
        self.btn_find_next.clicked.connect(self._search_next)
        self.search_layout.addWidget(self.btn_find_next)

        self.layout.addLayout(self.search_layout)

    def set_loading(self):
        self.badge_status.setText("SENDING")
        self.badge_status.setStyleSheet("""
            background: #1d2838;
            color: #569cd6;
            border: 1px solid #273a54;
            padding: 1px 6px;
            font-family: monospace;
            font-size: 10px;
        """)
        self.lbl_time.setText("...")
        self.lbl_size.setText("...")

    def display_response(self, resp: ResponseModel):
        self.current_response = resp

        if resp.status_code == 0:
            self.badge_status.setText("ERROR")
            self.badge_status.setStyleSheet("""
                background: #382020;
                color: #f48771;
                border: 1px solid #542828;
                font-family: monospace;
                font-size: 10px;
                font-weight: 600;
                padding: 1px 6px;
            """)
        else:
            status_text = f"{resp.status_code} {resp.reason_phrase}".strip()
            self.badge_status.setText(status_text)
            if resp.is_success:
                bg = "#1f2d22"
                fg = "#89d185"
                border = "#2a4430"
            elif resp.is_redirect:
                bg = "#1d2838"
                fg = "#569cd6"
                border = "#273a54"
            elif resp.is_client_error:
                bg = "#332b1a"
                fg = "#dcdcaa"
                border = "#4d3f20"
            else:
                bg = "#382020"
                fg = "#f48771"
                border = "#542828"

            self.badge_status.setStyleSheet(f"""
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                font-family: monospace;
                font-size: 10px;
                font-weight: 600;
                padding: 1px 6px;
            """)

        self.lbl_time.setText(f"{resp.elapsed_ms:.1f} ms")
        if resp.size_bytes < 1024:
            size_str = f"{resp.size_bytes} B"
        elif resp.size_bytes < 1024 * 1024:
            size_str = f"{resp.size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{resp.size_bytes / (1024 * 1024):.2f} MB"
        self.lbl_size.setText(size_str)

        self.editor_raw.setPlainText(resp.raw_text or "")

        pretty_text = resp.body_text or ""
        try:
            parsed_json = json.loads(pretty_text)
            pretty_text = json.dumps(parsed_json, indent=2, ensure_ascii=False)
            self.pretty_highlighter.active = True
        except Exception:
            self.pretty_highlighter.active = False
        self.editor_pretty.setPlainText(pretty_text)
        self.pretty_highlighter.rehighlight()

        self.headers_table.setRowCount(len(resp.headers))
        for row, (k, v) in enumerate(resp.headers):
            item_k = QtWidgets.QTableWidgetItem(k)
            item_v = QtWidgets.QTableWidgetItem(v)
            self.headers_table.setItem(row, 0, item_k)
            self.headers_table.setItem(row, 1, item_v)

    def _copy_raw(self):
        if self.current_response:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(self.current_response.raw_text or "")

    def _search_text(self, text: str):
        editor = self._current_active_editor()
        if not editor or not text:
            return
        cursor = editor.textCursor()
        cursor.setPosition(0)
        editor.setTextCursor(cursor)
        editor.find(text)

    def _search_next(self):
        editor = self._current_active_editor()
        text = self.txt_search.text()
        if editor and text:
            if not editor.find(text):
                cursor = editor.textCursor()
                cursor.setPosition(0)
                editor.setTextCursor(cursor)
                editor.find(text)

    def _current_active_editor(self) -> HttpCodeEditor:
        idx = self.tab_widget.currentIndex()
        if idx == 0:
            return self.editor_raw
        elif idx == 1:
            return self.editor_pretty
        return self.editor_raw
