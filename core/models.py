from dataclasses import dataclass, field
from typing import List, Tuple, Optional


@dataclass
class RequestModel:
    method: str = "GET"
    url: str = ""
    path: str = "/"
    http_version: str = "HTTP/1.1"
    headers: List[Tuple[str, str]] = field(default_factory=list)
    body: str = ""
    raw_text: str = ""

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        name_lower = name.lower()
        for k, v in self.headers:
            if k.lower() == name_lower:
                return v
        return default

    def set_header(self, name: str, value: str) -> None:
        name_lower = name.lower()
        new_headers = []
        replaced = False
        for k, v in self.headers:
            if k.lower() == name_lower:
                if not replaced:
                    new_headers.append((name, value))
                    replaced = True
            else:
                new_headers.append((k, v))
        if not replaced:
            new_headers.append((name, value))
        self.headers = new_headers


@dataclass
class ResponseModel:
    status_code: int = 0
    reason_phrase: str = ""
    http_version: str = "HTTP/1.1"
    headers: List[Tuple[str, str]] = field(default_factory=list)
    body_bytes: bytes = b""
    body_text: str = ""
    elapsed_ms: float = 0.0
    size_bytes: int = 0
    raw_text: str = ""
    error_message: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400

    @property
    def is_client_error(self) -> bool:
        return 400 <= self.status_code < 500

    @property
    def is_server_error(self) -> bool:
        return 500 <= self.status_code < 600

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        name_lower = name.lower()
        for k, v in self.headers:
            if k.lower() == name_lower:
                return v
        return default


@dataclass
class AutomatorTask:
    task_id: int
    payload: str
    request: RequestModel
    response: Optional[ResponseModel] = None
    status: str = "PENDING"
    error: Optional[str] = None


@dataclass
class HistoryItem:
    id: int
    timestamp: str
    method: str
    url: str
    status_code: int
    length: int
    elapsed_ms: float
    request_raw: str
    response_raw: str
    response_headers: List[Tuple[str, str]] = field(default_factory=list)
    response_body: str = ""
    reason_phrase: str = ""
