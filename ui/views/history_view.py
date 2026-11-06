from datetime import datetime
from core.qt_compat import QtWidgets, QtGui, Signal, Qt, QSize
from core.models import RequestModel, ResponseModel, HistoryItem
from ui.icons import Icons
from ui.components.code_editor import HttpCodeEditor
from ui.components.response_viewer import ResponseViewer


class HistoryView(QtWidgets.QWidget):
    send_to_repeater = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_items: list[HistoryItem] = []
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(4)

        self.top_bar = QtWidgets.QHBoxLayout()
        self.top_bar.setContentsMargins(0, 0, 0, 0)
        self.top_bar.setSpacing(6)

        self.lbl_title = QtWidgets.QLabel("FILTER:")
        self.lbl_title.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.top_bar.addWidget(self.lbl_title)

        self.txt_filter = QtWidgets.QLineEdit()
        self.txt_filter.setPlaceholderText("Filter by URL, method, status code...")
        self.txt_filter.textChanged.connect(self._apply_filter)
        self.top_bar.addWidget(self.txt_filter, 1)

        self.btn_send_to_repeater = QtWidgets.QPushButton("  Send to Repeater")
        self.btn_send_to_repeater.setIcon(Icons.get("arrow_right", color="#969696", size=12))
        self.btn_send_to_repeater.setIconSize(QSize(12, 12))
        self.btn_send_to_repeater.clicked.connect(self._on_send_to_repeater)
        self.top_bar.addWidget(self.btn_send_to_repeater)

        self.btn_clear = QtWidgets.QPushButton("  Clear History")
        self.btn_clear.setIcon(Icons.get("trash", color="#969696", size=12))
        self.btn_clear.setIconSize(QSize(12, 12))
        self.btn_clear.clicked.connect(self.clear_history)
        self.top_bar.addWidget(self.btn_clear)

        self.main_layout.addLayout(self.top_bar)

        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Vertical)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#", "TIME", "METHOD", "URL", "STATUS", "SIZE", "TIME (ms)"])
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.splitter.addWidget(self.table)

        self.lower_splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)

        self.req_box = QtWidgets.QWidget()
        self.req_layout = QtWidgets.QVBoxLayout(self.req_box)
        self.req_layout.setContentsMargins(0, 0, 0, 0)
        self.req_layout.setSpacing(2)
        self.lbl_req_p = QtWidgets.QLabel("SENT REQUEST")
        self.lbl_req_p.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.req_layout.addWidget(self.lbl_req_p)
        self.editor_req = HttpCodeEditor(read_only=True)
        self.req_layout.addWidget(self.editor_req)
        self.lower_splitter.addWidget(self.req_box)

        self.resp_viewer = ResponseViewer()
        self.lower_splitter.addWidget(self.resp_viewer)

        self.lower_splitter.setSizes([250, 350])
        self.splitter.addWidget(self.lower_splitter)

        self.splitter.setSizes([200, 250])
        self.main_layout.addWidget(self.splitter, 1)

    def add_record(self, req: RequestModel, resp: ResponseModel):
        idx = len(self.history_items) + 1
        now_str = datetime.now().strftime("%H:%M:%S")

        record = HistoryItem(
            id=idx,
            timestamp=now_str,
            method=req.method,
            url=req.url,
            status_code=resp.status_code,
            length=resp.size_bytes,
            elapsed_ms=resp.elapsed_ms,
            request_raw=req.raw_text,
            response_raw=resp.raw_text,
            response_headers=list(resp.headers),
            response_body=resp.body_text,
            reason_phrase=resp.reason_phrase,
        )
        self.history_items.append(record)

        row = self.table.rowCount()
        self.table.insertRow(row)

        item_id = QtWidgets.QTableWidgetItem(str(record.id))
        item_id.setData(Qt.ItemDataRole.UserRole, record.id)
        item_time = QtWidgets.QTableWidgetItem(record.timestamp)
        item_method = QtWidgets.QTableWidgetItem(record.method)
        item_url = QtWidgets.QTableWidgetItem(record.url)
        item_status = QtWidgets.QTableWidgetItem(str(record.status_code) if record.status_code > 0 else "ERR")

        if resp.is_success:
            item_status.setForeground(QtGui.QColor("#89d185"))
        elif resp.is_client_error:
            item_status.setForeground(QtGui.QColor("#dcdcaa"))
        elif resp.is_server_error:
            item_status.setForeground(QtGui.QColor("#f48771"))
        else:
            item_status.setForeground(QtGui.QColor("#569cd6"))

        item_len = QtWidgets.QTableWidgetItem(str(record.length))
        item_dur = QtWidgets.QTableWidgetItem(f"{record.elapsed_ms:.1f}")

        self.table.setItem(row, 0, item_id)
        self.table.setItem(row, 1, item_time)
        self.table.setItem(row, 2, item_method)
        self.table.setItem(row, 3, item_url)
        self.table.setItem(row, 4, item_status)
        self.table.setItem(row, 5, item_len)
        self.table.setItem(row, 6, item_dur)

    def _apply_filter(self, filter_text: str):
        filter_text = filter_text.strip().lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def clear_history(self):
        self.history_items.clear()
        self.table.setRowCount(0)
        self.editor_req.setPlainText("")
        self.resp_viewer.display_response(ResponseModel())

    def _on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table.item(row, 0)
        if not item_id:
            return
        rec_id = item_id.data(Qt.ItemDataRole.UserRole)
        if rec_id and rec_id <= len(self.history_items):
            rec = self.history_items[rec_id - 1]
            self.editor_req.setPlainText(rec.request_raw)
            dummy_resp = ResponseModel(
                status_code=rec.status_code,
                size_bytes=rec.length,
                elapsed_ms=rec.elapsed_ms,
                raw_text=rec.response_raw,
                body_text=rec.response_body,
                headers=list(rec.response_headers),
                reason_phrase=rec.reason_phrase,
            )
            self.resp_viewer.display_response(dummy_resp)

    def _on_send_to_repeater(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table.item(row, 0)
        if not item_id:
            return
        rec_id = item_id.data(Qt.ItemDataRole.UserRole)
        if rec_id and rec_id <= len(self.history_items):
            rec = self.history_items[rec_id - 1]
            self.send_to_repeater.emit(rec.request_raw, rec.url)
