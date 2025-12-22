#!/usr/bin/env python3
import os
import pathlib
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

YADISK_API = "https://cloud-api.yandex.net/v1/disk"
LOCAL_DIR = pathlib.Path(__file__).parent / "files_to_upload"
REMOTE_DIR = "/dz8_uploads"
YADISK_TOKEN = None


def y_headers(token: str) -> dict:
    return {"Authorization": f"OAuth {token}"}


def ensure_remote_folder(token: str, remote_path: str) -> None:
    url = f"{YADISK_API}/resources"
    r = requests.put(url, headers=y_headers(token), params={"path": remote_path}, timeout=20)
    if r.status_code in (201, 409):
        return
    raise RuntimeError(f"{r.status_code} {r.text}")


def list_files_remote(token: str, remote_path: str) -> set[str]:
    url = f"{YADISK_API}/resources"
    limit = 100
    offset = 0
    out: set[str] = set()

    while True:
        params = {"path": remote_path, "limit": limit, "offset": offset}
        r = requests.get(url, headers=y_headers(token), params=params, timeout=20)

        if r.status_code == 404:
            return set()
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code} {r.text}")

        data = r.json()
        embedded = data.get("_embedded", {})
        items = embedded.get("items", [])

        for it in items:
            if it.get("type") == "file":
                name = it.get("name")
                if name:
                    out.add(name)

        if len(items) < limit:
            break
        offset += limit

    return out


def get_upload_href(token: str, remote_file_path: str, overwrite: bool = True) -> str:
    url = f"{YADISK_API}/resources/upload"
    params = {"path": remote_file_path, "overwrite": "true" if overwrite else "false"}
    r = requests.get(url, headers=y_headers(token), params=params, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code} {r.text}")
    return r.json()["href"]


def upload_local_file(token: str, local_path: pathlib.Path, remote_dir: str) -> None:
    remote_file_path = f"{remote_dir}/{local_path.name}"
    href = get_upload_href(token, remote_file_path, overwrite=True)

    with local_path.open("rb") as f:
        r = requests.put(href, data=f, timeout=60)

    if r.status_code not in (201, 202):
        raise RuntimeError(f"{r.status_code} {r.text}")


def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def build_page(local_files: list[str], uploaded: set[str], message: str = "") -> str:
    rows = []
    for f in local_files:
        cls = "uploaded" if f in uploaded else ""
        rows.append(
            f"""
            <li class="{cls}">
              <label>
                <input type="checkbox" name="files" value="{html_escape(f)}">
                {html_escape(f)}
              </label>
            </li>
            """
        )

    msg_html = f'<div class="msg">{html_escape(message)}</div>' if message else ""

    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <title>ДЗ 8 — Яндекс.Диск</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    ul {{ padding-left: 18px; }}
    li {{ padding: 6px 10px; border-radius: 8px; margin: 6px 0; }}
    .uploaded {{ background: rgba(0, 200, 0, 0.25); }}
    .msg {{ padding: 10px 12px; border-radius: 10px; margin: 10px 0; background: rgba(0,0,0,0.06); }}
    button {{ padding: 10px 14px; border-radius: 10px; border: 1px solid #ccc; cursor: pointer; }}
    code {{ background: rgba(0,0,0,0.05); padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
  <h2>Загрузка файлов на Яндекс.Диск</h2>
  <div>
    Локальная папка: <code>{html_escape(str(LOCAL_DIR))}</code><br/>
    Папка на Диске: <code>{html_escape(REMOTE_DIR)}</code><br/>
    Уже загруженные файлы подсвечены зелёным.
  </div>

  {msg_html}

  {"<p>В папке files_to_upload нет файлов.</p>" if not local_files else f"""
  <form method="post" action="/upload">
    <ul>
      {''.join(rows)}
    </ul>
    <button type="submit">Загрузить выбранные</button>
  </form>
  """}
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: str, content_type: str = "text/plain; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != "/":
            self._send(404, "not found")
            return

        if not YADISK_TOKEN:
            self._send(500, "token not set")
            return

        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        local_files = sorted([p.name for p in LOCAL_DIR.iterdir() if p.is_file()])

        try:
            remote_files = list_files_remote(YADISK_TOKEN, REMOTE_DIR)
        except Exception as e:
            page = build_page(local_files, set(), message=str(e))
            self._send(200, page, "text/html; charset=utf-8")
            return

        uploaded = set(local_files) & remote_files
        page = build_page(local_files, uploaded)
        self._send(200, page, "text/html; charset=utf-8")

    def do_POST(self):
        if self.path != "/upload":
            self._send(404, "not found")
            return

        if not YADISK_TOKEN:
            self._send(500, "token not set")
            return

        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length)
        body = raw.decode("utf-8", errors="replace")

        parsed = urllib.parse.parse_qs(body)
        selected = parsed.get("files", [])

        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        local_files = sorted([p.name for p in LOCAL_DIR.iterdir() if p.is_file()])

        if not selected:
            try:
                remote_files = list_files_remote(YADISK_TOKEN, REMOTE_DIR)
            except Exception:
                remote_files = set()
            uploaded = set(local_files) & remote_files
            page = build_page(local_files, uploaded, message="no files selected")
            self._send(200, page, "text/html; charset=utf-8")
            return

        msgs = []
        try:
            ensure_remote_folder(YADISK_TOKEN, REMOTE_DIR)
            for name in selected:
                path = LOCAL_DIR / name
                if not path.exists():
                    msgs.append(f"missing {name}")
                    continue
                upload_local_file(YADISK_TOKEN, path, REMOTE_DIR)
                msgs.append(f"uploaded {name}")
        except Exception as e:
            msgs.append(str(e))

        try:
            remote_files = list_files_remote(YADISK_TOKEN, REMOTE_DIR)
        except Exception:
            remote_files = set()

        uploaded = set(local_files) & remote_files
        page = build_page(local_files, uploaded, message=" | ".join(msgs))
        self._send(200, page, "text/html; charset=utf-8")

    def log_message(self, fmt, *args):
        return


def main():
    global YADISK_TOKEN

    token = input("Вставьте OAuth-токен Яндекс.Диска и нажмите Enter: ").strip()
    if not token:
        raise SystemExit("empty token")
    YADISK_TOKEN = token

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)

    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8080"))

    httpd = HTTPServer((host, port), Handler)
    print(f"Open: http://{host}:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
