from core.qt_compat import QtWidgets, QtGui, Signal, Qt, QSize
from core.models import RequestModel, ResponseModel, AutomatorTask
from core.automator_engine import AutomatorRunner
from core.http_engine import HttpEngine
from ui.icons import Icons
from ui.components.code_editor import HttpCodeEditor
from ui.components.response_viewer import ResponseViewer


SAMPLE_AUTOMATE_TEMPLATE = """GET /get?id=§1§ HTTP/1.1
Host: httpbin.org
User-Agent: rChipe-Automate/1.0
Accept: application/json
Connection: close

"""

SAMPLE_PAYLOADS = """1\n2\n3\nadmin\ntest\nguest\nroot"""


class AutomatorView(QtWidgets.QWidget):
    send_to_repeater = Signal(str, str)
    request_completed = Signal(object, object)

    def __init__(self, http_engine: HttpEngine, parent=None):
        super().__init__(parent)
        self.http_engine = http_engine
        self.runner = AutomatorRunner(self.http_engine)
        self.tasks: list[AutomatorTask] = []

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(4)

        self.row1_layout = QtWidgets.QHBoxLayout()
        self.row1_layout.setContentsMargins(0, 0, 0, 0)
        self.row1_layout.setSpacing(4)

        self.lbl_target = QtWidgets.QLabel("TARGET:")
        self.lbl_target.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.row1_layout.addWidget(self.lbl_target)

        self.txt_target = QtWidgets.QLineEdit("https://httpbin.org")
        self.txt_target.setMinimumWidth(100)
        self.row1_layout.addWidget(self.txt_target, 1)

        self.btn_start = QtWidgets.QPushButton("  Start Batch")
        self.btn_start.setObjectName("btnSend")
        self.btn_start.setIcon(Icons.get("play", color="#ffffff", size=11))
        self.btn_start.setIconSize(QSize(11, 11))
        self.btn_start.clicked.connect(self.start_batch)
        self.row1_layout.addWidget(self.btn_start)

        self.btn_stop = QtWidgets.QPushButton("  Stop")
        self.btn_stop.setObjectName("btnCancel")
        self.btn_stop.setIcon(Icons.get("stop", color="#f8d7da", size=11))
        self.btn_stop.setIconSize(QSize(11, 11))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_batch)
        self.row1_layout.addWidget(self.btn_stop)

        self.main_layout.addLayout(self.row1_layout)

        self.row2_layout = QtWidgets.QHBoxLayout()
        self.row2_layout.setContentsMargins(0, 0, 0, 0)
        self.row2_layout.setSpacing(5)

        self.lbl_threads = QtWidgets.QLabel("Threads:")
        self.lbl_threads.setStyleSheet("color: #858585; font-size: 11px;")
        self.row2_layout.addWidget(self.lbl_threads)

        self.spin_threads = QtWidgets.QSpinBox()
        self.spin_threads.setRange(1, 30)
        self.spin_threads.setValue(5)
        self.spin_threads.setFixedWidth(48)
        self.row2_layout.addWidget(self.spin_threads)

        self.lbl_delay = QtWidgets.QLabel("Delay (ms):")
        self.lbl_delay.setStyleSheet("color: #858585; font-size: 11px;")
        self.row2_layout.addWidget(self.lbl_delay)

        self.spin_delay = QtWidgets.QSpinBox()
        self.spin_delay.setRange(0, 5000)
        self.spin_delay.setSingleStep(50)
        self.spin_delay.setValue(0)
        self.spin_delay.setFixedWidth(52)
        self.row2_layout.addWidget(self.spin_delay)

        self.btn_mark = QtWidgets.QPushButton("  Add Marker §")
        self.btn_mark.setIcon(Icons.get("marker", color="#969696", size=12))
        self.btn_mark.setIconSize(QSize(12, 12))
        self.btn_mark.setToolTip("Wrap selection with § marker for payload replacement")
        self.btn_mark.clicked.connect(self._add_marker)
        self.row2_layout.addWidget(self.btn_mark)

        self.btn_clear_markers = QtWidgets.QPushButton("  Clear Markers")
        self.btn_clear_markers.setIcon(Icons.get("cancel", color="#969696", size=11))
        self.btn_clear_markers.setIconSize(QSize(11, 11))
        self.btn_clear_markers.clicked.connect(self._clear_markers)
        self.row2_layout.addWidget(self.btn_clear_markers)

        self.row2_layout.addStretch()

        self.main_layout.addLayout(self.row2_layout)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.main_layout.addWidget(self.progress_bar)

        self.main_splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)

        self.left_tabs = QtWidgets.QTabWidget()

        self.tab_template = QtWidgets.QWidget()
        self.t_layout = QtWidgets.QVBoxLayout(self.tab_template)
        self.t_layout.setContentsMargins(2, 2, 2, 2)
        self.lbl_t_info = QtWidgets.QLabel("Template HTTP (use §param§ or {{payload}}):")
        self.lbl_t_info.setStyleSheet("color: #666666; font-size: 10px; font-family: monospace;")
        self.t_layout.addWidget(self.lbl_t_info)

        self.editor_template = HttpCodeEditor()
        self.editor_template.setPlainText(SAMPLE_AUTOMATE_TEMPLATE)
        self.t_layout.addWidget(self.editor_template)
        self.left_tabs.addTab(self.tab_template, "HTTP Template")

        self.tab_payloads = QtWidgets.QWidget()
        self.p_layout = QtWidgets.QVBoxLayout(self.tab_payloads)
        self.p_layout.setContentsMargins(2, 2, 2, 2)

        self.p_header = QtWidgets.QHBoxLayout()
        self.lbl_payload_count = QtWidgets.QLabel("Payload list (one per line):")
        self.lbl_payload_count.setStyleSheet("color: #858585; font-size: 10px;")
        self.p_header.addWidget(self.lbl_payload_count)
        self.p_header.addStretch()

        self.btn_load_file = QtWidgets.QPushButton("  Load File...")
        self.btn_load_file.setIcon(Icons.get("file", color="#969696", size=11))
        self.btn_load_file.setIconSize(QSize(11, 11))
        self.btn_load_file.clicked.connect(self._load_payloads_file)
        self.p_header.addWidget(self.btn_load_file)

        self.p_layout.addLayout(self.p_header)

        self.editor_payloads = QtWidgets.QPlainTextEdit()
        self.editor_payloads.setPlainText(SAMPLE_PAYLOADS)
        self.editor_payloads.textChanged.connect(self._update_payload_count)
        self.p_layout.addWidget(self.editor_payloads)
        self.left_tabs.addTab(self.tab_payloads, "Payloads")

        self.main_splitter.addWidget(self.left_tabs)

        self.results_splitter = QtWidgets.QSplitter(Qt.Orientation.Vertical)

        self.table_panel = QtWidgets.QWidget()
        self.tbl_layout = QtWidgets.QVBoxLayout(self.table_panel)
        self.tbl_layout.setContentsMargins(0, 0, 0, 0)
        self.tbl_layout.setSpacing(2)

        self.tbl_header = QtWidgets.QHBoxLayout()
        self.lbl_results = QtWidgets.QLabel("RESULTS")
        self.lbl_results.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.tbl_header.addWidget(self.lbl_results)
        self.tbl_header.addStretch()

        self.btn_send_selected_to_repeater = QtWidgets.QPushButton("  Send to Repeater")
        self.btn_send_selected_to_repeater.setIcon(Icons.get("arrow_right", color="#969696", size=12))
        self.btn_send_selected_to_repeater.setIconSize(QSize(12, 12))
        self.btn_send_selected_to_repeater.clicked.connect(self._send_selected_to_repeater)
        self.tbl_header.addWidget(self.btn_send_selected_to_repeater)

        self.tbl_layout.addLayout(self.tbl_header)

        self.table_results = QtWidgets.QTableWidget()
        self.table_results.setColumnCount(6)
        self.table_results.setHorizontalHeaderLabels(["#", "PAYLOAD", "STATUS", "LENGTH", "TIME (ms)", "ERROR"])
        self.table_results.horizontalHeader().setStretchLastSection(True)
        self.table_results.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table_results.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table_results.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_results.setSortingEnabled(True)
        self.table_results.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.tbl_layout.addWidget(self.table_results)

        self.results_splitter.addWidget(self.table_panel)

        self.inspector_panel = ResponseViewer()
        self.results_splitter.addWidget(self.inspector_panel)
        self.results_splitter.setSizes([180, 200])

        self.main_splitter.addWidget(self.results_splitter)
        self.main_splitter.setSizes([300, 420])

        self.main_layout.addWidget(self.main_splitter, 1)

        self._update_payload_count()

    def _connect_signals(self):
        self.runner.signals.task_completed.connect(self._on_task_completed)
        self.runner.signals.progress.connect(self._on_progress)
        self.runner.signals.finished.connect(self._on_batch_finished)
        self.runner.signals.stopped.connect(self._on_batch_finished)

    def _add_marker(self):
        cursor = self.editor_template.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"§{selected}§")
        else:
            cursor.insertText("§param§")

    def _clear_markers(self):
        text = self.editor_template.toPlainText()
        cleaned = text.replace("§", "")
        self.editor_template.setPlainText(cleaned)

    def _update_payload_count(self):
        lines = [line.strip() for line in self.editor_payloads.toPlainText().split("\n") if line.strip()]
        self.lbl_payload_count.setText(f"Payloads: {len(lines)}")

    def _load_payloads_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Payload File", "", "Text Files (*.txt *.csv *.lst);;All Files (*.*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.editor_payloads.setPlainText(content)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "File Error", str(e))

    def set_template_from_raw(self, raw_http: str, target: str = ""):
        self.editor_template.setPlainText(raw_http)
        if target:
            self.txt_target.setText(target)

    def start_batch(self):
        raw_tmpl = self.editor_template.toPlainText()
        target = self.txt_target.text().strip()
        payloads = [line.strip() for line in self.editor_payloads.toPlainText().split("\n") if line.strip()]

        if not payloads:
            QtWidgets.QMessageBox.warning(self, "No Payloads", "Enter at least one payload.")
            return

        if "§" not in raw_tmpl and "{{payload}}" not in raw_tmpl:
            QtWidgets.QMessageBox.warning(
                self,
                "No Payload Marker",
                "Add §param§ or {{payload}} to the HTTP template.",
            )
            return

        self.table_results.setSortingEnabled(False)
        self.table_results.setRowCount(0)
        try:
            self.tasks = self.runner.setup(raw_tmpl, target, payloads)
        except ValueError as error:
            QtWidgets.QMessageBox.warning(self, "Invalid Template", str(error))
            return

        self.table_results.setRowCount(len(self.tasks))
        for row, t in enumerate(self.tasks):
            item_id = QtWidgets.QTableWidgetItem(str(t.task_id))
            item_id.setData(Qt.ItemDataRole.UserRole, t.task_id)
            item_payload = QtWidgets.QTableWidgetItem(t.payload)
            item_status = QtWidgets.QTableWidgetItem("Pending")
            item_len = QtWidgets.QTableWidgetItem("-")
            item_time = QtWidgets.QTableWidgetItem("-")
            item_err = QtWidgets.QTableWidgetItem("")

            self.table_results.setItem(row, 0, item_id)
            self.table_results.setItem(row, 1, item_payload)
            self.table_results.setItem(row, 2, item_status)
            self.table_results.setItem(row, 3, item_len)
            self.table_results.setItem(row, 4, item_time)
            self.table_results.setItem(row, 5, item_err)

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.progress_bar.setMaximum(len(payloads))
        self.progress_bar.setValue(0)

        concurrency = self.spin_threads.value()
        delay_ms = self.spin_delay.value()
        self.runner.start(max_concurrency=concurrency, delay_ms=delay_ms)

    def stop_batch(self):
        self.runner.cancel()
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_task_completed(self, task_id: int, resp: ResponseModel):
        row = -1
        for candidate_row in range(self.table_results.rowCount()):
            item = self.table_results.item(candidate_row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == task_id:
                row = candidate_row
                break
        if row < self.table_results.rowCount():
            task = next((item for item in self.tasks if item.task_id == task_id), None)
            if task:
                task.response = resp
                self.request_completed.emit(task.request, resp)
            item_status = self.table_results.item(row, 2)
            item_len = self.table_results.item(row, 3)
            item_time = self.table_results.item(row, 4)
            item_err = self.table_results.item(row, 5)

            if resp.status_code > 0:
                item_status.setText(str(resp.status_code))
                if resp.is_success:
                    item_status.setForeground(QtGui.QColor("#89d185"))
                elif resp.is_client_error:
                    item_status.setForeground(QtGui.QColor("#dcdcaa"))
                elif resp.is_server_error:
                    item_status.setForeground(QtGui.QColor("#f48771"))
                else:
                    item_status.setForeground(QtGui.QColor("#569cd6"))

                item_len.setText(str(resp.size_bytes))
                item_time.setText(f"{resp.elapsed_ms:.1f}")
                item_err.setText("")
            else:
                item_status.setText("ERR")
                item_status.setForeground(QtGui.QColor("#f48771"))
                item_err.setText(resp.error_message or "Error")

    def _on_progress(self, current: int, total: int):
        self.progress_bar.setValue(current)

    def _on_batch_finished(self):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.table_results.setSortingEnabled(True)

    def _on_table_selection_changed(self):
        selected_rows = self.table_results.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table_results.item(row, 0)
        if not item_id:
            return
        task_id = item_id.data(Qt.ItemDataRole.UserRole)
        if task_id and task_id <= len(self.tasks):
            task = self.tasks[task_id - 1]
            if task.response:
                self.inspector_panel.display_response(task.response)

    def _send_selected_to_repeater(self):
        selected_rows = self.table_results.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table_results.item(row, 0)
        if not item_id:
            return
        task_id = item_id.data(Qt.ItemDataRole.UserRole)
        if task_id and task_id <= len(self.tasks):
            task = self.tasks[task_id - 1]
            self.send_to_repeater.emit(task.request.raw_text, self.txt_target.text().strip())
