import json
from urllib.parse import urlparse
from core.qt_compat import QtWidgets, QtGui, Signal, Qt, QThreadPool, QSize
from core.models import RequestModel, ResponseModel
from core.raw_parser import RawHttpParser
from core.http_engine import HttpEngine, HttpRequestWorker
from utils.curl_converter import curl_to_raw_http, raw_http_to_curl
from ui.icons import Icons
from ui.components.code_editor import HttpCodeEditor
from ui.components.response_viewer import ResponseViewer


DEFAULT_SAMPLE_REQUEST = """GET /get?test=poc HTTP/1.1
Host: httpbin.org
User-Agent: rChipe/1.0
Accept: application/json
Connection: close

"""


class RepeaterView(QtWidgets.QWidget):
    request_completed = Signal(object, object)

    def __init__(self, http_engine: HttpEngine, thread_pool: QThreadPool, parent=None):
        super().__init__(parent)
        self.http_engine = http_engine
        self.thread_pool = thread_pool
        self.current_worker = None

        self._init_ui()

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

        self.txt_target = QtWidgets.QLineEdit()
        self.txt_target.setPlaceholderText("https://example.com (or inferred from Host header)")
        self.txt_target.setText("https://httpbin.org/get?test=poc")
        self.txt_target.setMinimumWidth(100)
        self.row1_layout.addWidget(self.txt_target, 1)
        self.txt_target.textEdited.connect(self._sync_request_from_url)

        self.btn_send = QtWidgets.QPushButton("  Send")
        self.btn_send.setObjectName("btnSend")
        self.btn_send.setIcon(Icons.get("send", color="#ffffff", size=12))
        self.btn_send.setIconSize(QSize(12, 12))
        self.btn_send.setToolTip("Send request (Ctrl+Enter)")
        self.btn_send.clicked.connect(self.send_request)
        self.row1_layout.addWidget(self.btn_send)

        self.btn_cancel = QtWidgets.QPushButton("  Cancel")
        self.btn_cancel.setObjectName("btnCancel")
        self.btn_cancel.setIcon(Icons.get("cancel", color="#f8d7da", size=12))
        self.btn_cancel.setIconSize(QSize(12, 12))
        self.btn_cancel.setToolTip("Cancel in-flight request")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_request)
        self.row1_layout.addWidget(self.btn_cancel)

        self.btn_layout_toggle = QtWidgets.QPushButton("  Split")
        self.btn_layout_toggle.setIcon(Icons.get("split", color="#969696", size=12))
        self.btn_layout_toggle.setIconSize(QSize(12, 12))
        self.btn_layout_toggle.setToolTip("Toggle Horizontal / Vertical Split")
        self.btn_layout_toggle.clicked.connect(self._toggle_splitter_orientation)
        self.row1_layout.addWidget(self.btn_layout_toggle)

        self.main_layout.addLayout(self.row1_layout)

        self.row2_layout = QtWidgets.QHBoxLayout()
        self.row2_layout.setContentsMargins(0, 0, 0, 0)
        self.row2_layout.setSpacing(4)

        self.btn_update_cl = QtWidgets.QPushButton("  Content-Length")
        self.btn_update_cl.setIcon(Icons.get("hash", color="#969696", size=12))
        self.btn_update_cl.setIconSize(QSize(12, 12))
        self.btn_update_cl.setToolTip("Calculate and update Content-Length header")
        self.btn_update_cl.clicked.connect(self._auto_update_content_length)
        self.row2_layout.addWidget(self.btn_update_cl)

        self.btn_format_json = QtWidgets.QPushButton("  Prettify JSON")
        self.btn_format_json.setIcon(Icons.get("json", color="#969696", size=12))
        self.btn_format_json.setIconSize(QSize(12, 12))
        self.btn_format_json.setToolTip("Format and indent body if JSON")
        self.btn_format_json.clicked.connect(self._format_json_body)
        self.row2_layout.addWidget(self.btn_format_json)

        self.btn_curl_import = QtWidgets.QPushButton("  Import cURL")
        self.btn_curl_import.setIcon(Icons.get("import", color="#969696", size=12))
        self.btn_curl_import.setIconSize(QSize(12, 12))
        self.btn_curl_import.setToolTip("Parse cURL command into Raw HTTP")
        self.btn_curl_import.clicked.connect(self._import_from_curl)
        self.row2_layout.addWidget(self.btn_curl_import)

        self.btn_curl_copy = QtWidgets.QPushButton("  Copy cURL")
        self.btn_curl_copy.setIcon(Icons.get("copy", color="#969696", size=12))
        self.btn_curl_copy.setIconSize(QSize(12, 12))
        self.btn_curl_copy.setToolTip("Export current request to cURL command")
        self.btn_curl_copy.clicked.connect(self._copy_as_curl)
        self.row2_layout.addWidget(self.btn_curl_copy)

        self.row2_layout.addStretch()

        self.btn_wrap = QtWidgets.QPushButton("  Wrap")
        self.btn_wrap.setIcon(Icons.get("wrap", color="#969696", size=12))
        self.btn_wrap.setIconSize(QSize(12, 12))
        self.btn_wrap.setCheckable(True)
        self.btn_wrap.setToolTip("Toggle soft line wrap")
        self.btn_wrap.toggled.connect(self._toggle_wrap)
        self.row2_layout.addWidget(self.btn_wrap)

        self.main_layout.addLayout(self.row2_layout)

        self.splitter = QtWidgets.QSplitter(Qt.Orientation.Horizontal)

        self.req_container = QtWidgets.QWidget()
        self.req_layout = QtWidgets.QVBoxLayout(self.req_container)
        self.req_layout.setContentsMargins(0, 0, 0, 0)
        self.req_layout.setSpacing(2)

        self.lbl_req = QtWidgets.QLabel("REQUEST")
        self.lbl_req.setStyleSheet("font-weight: 600; color: #858585; font-size: 10px; letter-spacing: 0.5px;")
        self.req_layout.addWidget(self.lbl_req)

        self.editor_request = HttpCodeEditor()
        self.editor_request.setPlainText(DEFAULT_SAMPLE_REQUEST)
        self.editor_request.send_requested.connect(self.send_request)
        self.editor_request.textChanged.connect(self._sync_url_from_request)
        self.req_layout.addWidget(self.editor_request)

        self.splitter.addWidget(self.req_container)

        self.response_viewer = ResponseViewer()
        self.splitter.addWidget(self.response_viewer)

        self.splitter.setSizes([350, 350])

        self.main_layout.addWidget(self.splitter, 1)

    def send_request(self):
        raw_text = self.editor_request.toPlainText()
        target = self.txt_target.text().strip()

        req_model = RawHttpParser.parse_request(raw_text, target)

        if not target and req_model.url:
            from urllib.parse import urlparse
            p = urlparse(req_model.url)
            self.txt_target.setText(f"{p.scheme}://{p.netloc}")

        self.btn_send.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.response_viewer.set_loading()

        worker = HttpRequestWorker(self.http_engine, req_model)
        worker.signals.finished.connect(lambda resp: self._on_request_finished(req_model, resp))
        self.current_worker = worker
        self.thread_pool.start(worker)

    def _sync_request_from_url(self, url_text: str):
        url_text = url_text.strip()
        if not url_text:
            return

        parsed = urlparse(url_text)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return

        raw_text = self.editor_request.toPlainText()
        req_model = RawHttpParser.parse_request(raw_text)
        request_path = parsed.path or "/"
        if parsed.query:
            request_path += f"?" + parsed.query

        req_model.path = request_path
        req_model.url = url_text
        headers = []
        host_found = False
        for name, value in req_model.headers:
            if name.lower() == "host":
                if not host_found:
                    headers.append(("Host", parsed.netloc))
                host_found = True
            else:
                headers.append((name, value))
        if not host_found:
            headers.insert(0, ("Host", parsed.netloc))
        req_model.headers = headers

        serialized = RawHttpParser.serialize_request(req_model)
        if serialized != raw_text:
            self.editor_request.blockSignals(True)
            self.editor_request.setPlainText(serialized)
            self.editor_request.blockSignals(False)

    def _sync_url_from_request(self):
        raw_text = self.editor_request.toPlainText()
        req_model = RawHttpParser.parse_request(raw_text)
        host = req_model.get_header("Host")
        if not host:
            return

        current = urlparse(self.txt_target.text().strip())
        scheme = current.scheme if current.scheme in ("http", "https") else "https"
        url = f"{scheme}://{host}{req_model.path}"
        if self.txt_target.text().strip() != url:
            self.txt_target.setText(url)

    def _on_request_finished(self, req: RequestModel, resp: ResponseModel):
        self.btn_send.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.current_worker = None
        self.response_viewer.display_response(resp)
        self.request_completed.emit(req, resp)

    def cancel_request(self):
        self.btn_send.setEnabled(True)
        self.btn_cancel.setEnabled(False)

    def load_raw_request(self, raw_text: str, target: str = ""):
        self.editor_request.setPlainText(raw_text)
        if target:
            self.txt_target.setText(target)

    def _auto_update_content_length(self):
        raw_text = self.editor_request.toPlainText()
        target = self.txt_target.text().strip()
        req_model = RawHttpParser.parse_request(raw_text, target)
        updated_raw = RawHttpParser.serialize_request(req_model, update_content_length=True)
        self.editor_request.setPlainText(updated_raw)

    def _format_json_body(self):
        raw_text = self.editor_request.toPlainText()
        target = self.txt_target.text().strip()
        req_model = RawHttpParser.parse_request(raw_text, target)
        if req_model.body:
            try:
                parsed = json.loads(req_model.body)
                req_model.body = json.dumps(parsed, indent=2, ensure_ascii=False)
                updated_raw = RawHttpParser.serialize_request(req_model, update_content_length=True)
                self.editor_request.setPlainText(updated_raw)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Invalid JSON", f"Body is not valid JSON:\n{str(e)}")

    def _import_from_curl(self):
        clipboard = QtWidgets.QApplication.clipboard()
        curl_text = clipboard.text().strip()
        if not curl_text or "curl" not in curl_text.lower():
            text, ok = QtWidgets.QInputDialog.getMultiLineText(
                self, "Import cURL", "Paste cURL command below:"
            )
            if ok and text:
                curl_text = text.strip()
            else:
                return

        target, raw_http = curl_to_raw_http(curl_text)
        if raw_http:
            self.editor_request.setPlainText(raw_http)
            if target:
                self.txt_target.setText(target)

    def _copy_as_curl(self):
        raw_text = self.editor_request.toPlainText()
        target = self.txt_target.text().strip()
        curl_cmd = raw_http_to_curl(raw_text, target)
        if curl_cmd:
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(curl_cmd)
            QtWidgets.QToolTip.showText(
                QtGui.QCursor.pos(), "cURL command copied to clipboard", self.btn_curl_copy
            )

    def _toggle_splitter_orientation(self):
        if self.splitter.orientation() == Qt.Orientation.Horizontal:
            self.splitter.setOrientation(Qt.Orientation.Vertical)
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)

    def _toggle_wrap(self, checked: bool):
        mode = QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth if checked else QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap
        self.editor_request.setLineWrapMode(mode)
