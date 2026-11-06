import time
import httpx
from typing import Optional, Dict, Any, List, Tuple
from core.models import RequestModel, ResponseModel
from core.qt_compat import QObject, QRunnable, Signal, Slot


class RequestSignals(QObject):
    started = Signal()
    finished = Signal(object)
    error = Signal(str)


class HttpEngine:
    def __init__(
        self,
        verify_ssl: bool = False,
        follow_redirects: bool = False,
        timeout: float = 15.0,
        proxy: Optional[str] = None,
    ):
        self.verify_ssl = verify_ssl
        self.follow_redirects = follow_redirects
        self.timeout = timeout
        self.proxy = proxy

    def execute(self, req: RequestModel) -> ResponseModel:
        """
        Executes a single HTTP request synchronously.
        """
        start_time = time.perf_counter()

        req_headers = []
        for k, v in req.headers:
            req_headers.append((k, v))

        body_bytes = req.body.encode("utf-8") if req.body else None

        client_kwargs: Dict[str, Any] = {
            "verify": self.verify_ssl,
            "follow_redirects": self.follow_redirects,
            "timeout": self.timeout,
        }
        if self.proxy:
            client_kwargs["proxy"] = self.proxy

        try:
            with httpx.Client(**client_kwargs) as client:
                http_resp = client.request(
                    method=req.method,
                    url=req.url,
                    headers=req_headers,
                    content=body_bytes,
                )

                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                resp_headers: List[Tuple[str, str]] = list(http_resp.headers.raw)
                formatted_headers: List[Tuple[str, str]] = []
                for k, v in resp_headers:
                    formatted_headers.append((k.decode("latin1", errors="replace"), v.decode("latin1", errors="replace")))

                body_content = http_resp.content
                try:
                    body_text = http_resp.text
                except Exception:
                    body_text = body_content.decode("latin1", errors="replace")

                model = ResponseModel(
                    status_code=http_resp.status_code,
                    reason_phrase=http_resp.reason_phrase,
                    http_version=http_resp.http_version,
                    headers=formatted_headers,
                    body_bytes=body_content,
                    body_text=body_text,
                    elapsed_ms=elapsed_ms,
                    size_bytes=len(body_content),
                )
                model.raw_text = RawHttpParser.serialize_response(model)
                return model

        except Exception as ex:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            err_msg = f"{type(ex).__name__}: {str(ex)}"
            model = ResponseModel(
                status_code=0,
                reason_phrase="Network Error",
                http_version="HTTP/1.1",
                headers=[],
                body_bytes=b"",
                body_text=f"Error executing request:\n{err_msg}",
                elapsed_ms=elapsed_ms,
                size_bytes=0,
                error_message=err_msg,
            )
            model.raw_text = f"HTTP/1.1 000 Error\r\n\r\n{err_msg}"
            return model


class HttpRequestWorker(QRunnable):
    """
    Worker task for executing an HTTP request in a background thread via QThreadPool.
    """
    def __init__(self, engine: HttpEngine, request: RequestModel):
        super().__init__()
        self.engine = engine
        self.request = request
        self.signals = RequestSignals()

    @Slot()
    def run(self):
        self.signals.started.emit()
        response = self.engine.execute(self.request)
        self.signals.finished.emit(response)
