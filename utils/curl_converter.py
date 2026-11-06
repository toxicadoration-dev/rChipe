import shlex
import re
from typing import Tuple, List, Optional
from core.raw_parser import RawHttpParser


def curl_to_raw_http(curl_cmd: str) -> Tuple[str, str]:
    """
    Parses a curl command line and returns (target_url, raw_http_text).
    """
    curl_cmd = curl_cmd.strip()
    if curl_cmd.startswith("$ "):
        curl_cmd = curl_cmd[2:].strip()

    clean_cmd = re.sub(r"\\\s*\n", " ", curl_cmd)

    try:
        tokens = shlex.split(clean_cmd)
    except Exception:
        tokens = clean_cmd.split()

    if not tokens:
        return "", ""

    if tokens[0].lower() == "curl":
        tokens = tokens[1:]

    method = "GET"
    url = ""
    headers: List[Tuple[str, str]] = []
    data: Optional[str] = None

    idx = 0
    while idx < len(tokens):
        token = tokens[idx]

        if token in ("-X", "--request") and idx + 1 < len(tokens):
            method = tokens[idx + 1].upper()
            idx += 2
        elif token in ("-H", "--header") and idx + 1 < len(tokens):
            header_str = tokens[idx + 1]
            if ":" in header_str:
                h_name, h_val = header_str.split(":", 1)
                headers.append((h_name.strip(), h_val.strip()))
            idx += 2
        elif token in ("-d", "--data", "--data-raw", "--data-binary", "--data-ascii") and idx + 1 < len(tokens):
            data = tokens[idx + 1]
            if method == "GET":
                method = "POST"
            idx += 2
        elif token in ("-A", "--user-agent") and idx + 1 < len(tokens):
            headers.append(("User-Agent", tokens[idx + 1]))
            idx += 2
        elif token in ("-u", "--user") and idx + 1 < len(tokens):
            import base64
            encoded = base64.b64encode(tokens[idx + 1].encode()).decode()
            headers.append(("Authorization", f"Basic {encoded}"))
            idx += 2
        elif token.startswith("http://") or token.startswith("https://"):
            url = token
            idx += 1
        elif not token.startswith("-") and not url:
            url = token
            idx += 1
        else:
            idx += 1

    from urllib.parse import urlparse
    parsed = urlparse(url)
    target_base = f"{parsed.scheme}://{parsed.netloc}" if parsed.netloc else url
    path = parsed.path or "/"
    if parsed.query:
        path += f"?{parsed.query}"

    has_host = any(k.lower() == "host" for k, v in headers)
    if not has_host and parsed.netloc:
        headers.insert(0, ("Host", parsed.netloc))

    if data is not None:
        has_cl = any(k.lower() == "content-length" for k, v in headers)
        if not has_cl:
            headers.append(("Content-Length", str(len(data.encode("utf-8")))))

    lines = [f"{method} {path} HTTP/1.1"]
    for k, v in headers:
        lines.append(f"{k}: {v}")

    raw_req = "\r\n".join(lines) + "\r\n\r\n" + (data or "")
    return target_base, raw_req


def raw_http_to_curl(raw_text: str, target_override: Optional[str] = None) -> str:
    """
    Converts raw HTTP text to a single reproducible curl command.
    """
    req = RawHttpParser.parse_request(raw_text, target_override)
    if not req.url:
        return ""

    cmd_parts = ["curl", "-X", req.method, f"'{req.url}'"]

    for k, v in req.headers:
        if k.lower() in ("host", "content-length"):
            continue
        clean_v = v.replace("'", "'\\''")
        cmd_parts.extend(["-H", f"'{k}: {clean_v}'"])

    if req.body:
        clean_body = req.body.replace("'", "'\\''")
        cmd_parts.extend(["--data-raw", f"'{clean_body}'"])

    return " ".join(cmd_parts)
