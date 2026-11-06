from urllib.parse import urlparse
from typing import Tuple, List, Optional
from core.models import RequestModel


class RawHttpParser:
    @staticmethod
    def parse_request(raw_text: str, target_override: Optional[str] = None) -> RequestModel:
        """
        Parses raw HTTP request string into a RequestModel.
        Accepts both \r\n and \n line endings.
        """
        raw_text = raw_text.strip("\r\n")
        if not raw_text:
            return RequestModel(raw_text="")

        if "\r\n\r\n" in raw_text:
            header_section, body = raw_text.split("\r\n\r\n", 1)
        elif "\n\n" in raw_text:
            header_section, body = raw_text.split("\n\n", 1)
        else:
            header_section = raw_text
            body = ""

        lines = [line.strip("\r") for line in header_section.split("\n") if line.strip("\r")]
        if not lines:
            return RequestModel(raw_text=raw_text, body=body)

        request_line = lines[0].strip()
        parts = request_line.split()
        method = parts[0].upper() if len(parts) >= 1 else "GET"
        path = parts[1] if len(parts) >= 2 else "/"
        http_version = parts[2] if len(parts) >= 3 else "HTTP/1.1"

        headers: List[Tuple[str, str]] = []
        host_header = None

        for line in lines[1:]:
            if ":" in line:
                name, val = line.split(":", 1)
                name = name.strip()
                val = val.strip()
                headers.append((name, val))
                if name.lower() == "host":
                    host_header = val

        full_url_override = ""
        if target_override and target_override.strip():
            override = target_override.strip()
            parsed_override = urlparse(override)
            override_path = parsed_override.path.rstrip("/")
            if override_path or parsed_override.query:
                full_url_override = override
            else:
                full_url_override = ""
            base_url = override.rstrip("/")
        elif host_header:
            if host_header.startswith("127.0.0.1") or host_header.startswith("localhost"):
                scheme = "http"
            else:
                scheme = "https"
            base_url = f"{scheme}://{host_header}".rstrip("/")
        else:
            base_url = "http://localhost"

        if path.startswith("http://") or path.startswith("https://"):
            full_url = path
            parsed = urlparse(path)
            path = parsed.path or "/"
            if parsed.query:
                path += f"?{parsed.query}"
        else:
            if not path.startswith("/"):
                path = "/" + path
            if full_url_override:
                full_url = full_url_override
                parsed = urlparse(full_url_override)
                path = parsed.path or "/"
                if parsed.query:
                    path += f"?{parsed.query}"
            else:
                full_url = f"{base_url}{path}"

        return RequestModel(
            method=method,
            url=full_url,
            path=path,
            http_version=http_version,
            headers=headers,
            body=body,
            raw_text=raw_text,
        )

    @staticmethod
    def serialize_request(model: RequestModel, update_content_length: bool = False) -> str:
        """
        Serializes a RequestModel back into a standard raw HTTP string.
        """
        headers = list(model.headers)
        body = model.body or ""
        body_bytes = body.encode("utf-8")

        if update_content_length:
            content_length = str(len(body_bytes))
            cl_found = False
            new_headers = []
            for k, v in headers:
                if k.lower() == "content-length":
                    new_headers.append((k, content_length))
                    cl_found = True
                else:
                    new_headers.append((k, v))
            if not cl_found and (body_bytes or model.method in ("POST", "PUT", "PATCH")):
                new_headers.append(("Content-Length", content_length))
            headers = new_headers

        lines = [f"{model.method} {model.path} {model.http_version}"]
        for k, v in headers:
            lines.append(f"{k}: {v}")

        raw_req = "\r\n".join(lines) + "\r\n\r\n" + body
        return raw_req

    @staticmethod
    def serialize_response(model: ResponseModel) -> str:
        """
        Serializes a ResponseModel into raw HTTP response text.
        """
        status_line = f"{model.http_version} {model.status_code} {model.reason_phrase}".strip()
        lines = [status_line]
        for k, v in model.headers:
            lines.append(f"{k}: {v}")
        return "\r\n".join(lines) + "\r\n\r\n" + (model.body_text or "")
