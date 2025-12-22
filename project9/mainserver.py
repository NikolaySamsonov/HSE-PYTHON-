from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import json
import os

TASKS_FILE = "tasks.txt"
ALLOWED_PRIORITIES = {"low", "normal", "high"}

TASKS = []
NEXT_TASK_ID = 1


def load_tasks_from_file():
    global TASKS, NEXT_TASK_ID

    if not os.path.exists(TASKS_FILE):
        TASKS = []
        NEXT_TASK_ID = 1
        return

    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                TASKS = []
                NEXT_TASK_ID = 1
                return

            data = json.loads(raw)
            if not isinstance(data, list):
                TASKS = []
                NEXT_TASK_ID = 1
                return

            restored = []
            max_id = 0
            for item in data:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                priority = item.get("priority")
                is_done = item.get("isDone")
                task_id = item.get("id")
                if not isinstance(title, str):
                    continue
                if not isinstance(priority, str):
                    continue
                if not isinstance(is_done, bool):
                    continue
                if not isinstance(task_id, int):
                    continue

                restored.append({
                    "title": title,
                    "priority": priority,
                    "isDone": is_done,
                    "id": task_id
                })
                max_id = max(max_id, task_id)

            TASKS = restored
            NEXT_TASK_ID = max_id + 1

    except Exception:
        TASKS = []
        NEXT_TASK_ID = 1


def save_tasks_to_file():
    tmp = TASKS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(TASKS, f, ensure_ascii=False, indent=2)
    os.replace(tmp, TASKS_FILE)


class SimpleRESTHandler(BaseHTTPRequestHandler):
    def _read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _send_json(self, data, status=200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_empty(self, status=200):
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _error(self, status, msg):
        self._send_json({"error": msg}, status=status)

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = [p for p in parsed.path.split("/") if p]

        if parsed.path == "/tasks":
            return self.create_task()

        if len(parts) == 3 and parts[0] == "tasks" and parts[2] == "complete":
            return self.complete_task(parts[1])

        self._send_empty(404)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/tasks":
            return self.list_tasks()

        self._send_empty(404)

    def create_task(self):
        global NEXT_TASK_ID
        data = self._read_json_body()

        if not isinstance(data, dict):
            return self._error(400, "JSON body must be an object")

        title = data.get("title")
        priority = data.get("priority")

        if not isinstance(title, str) or not title.strip():
            return self._error(400, "Field 'title' must be a non-empty string")

        if not isinstance(priority, str) or priority not in ALLOWED_PRIORITIES:
            return self._error(400, "Field 'priority' must be one of: low, normal, high")

        task = {
            "title": title.strip(),
            "priority": priority,
            "isDone": False,
            "id": NEXT_TASK_ID
        }

        NEXT_TASK_ID += 1
        TASKS.append(task)
        save_tasks_to_file()

        return self._send_json(task, status=200)

    def list_tasks(self):
        return self._send_json(TASKS, status=200)

    def complete_task(self, task_id_str):
        try:
            task_id = int(task_id_str)
        except ValueError:
            return self._send_empty(404)

        for task in TASKS:
            if task["id"] == task_id:
                if not task["isDone"]:
                    task["isDone"] = True
                    save_tasks_to_file()
                return self._send_empty(200)

        return self._send_empty(404)

    def log_message(self, format, *args):
        return


def run(host="127.0.0.1", port=8080):
    load_tasks_from_file()
    print(f"Serving on http://{host}:{port}")
    print(f"Data file: {os.path.abspath(TASKS_FILE)}")
    server = HTTPServer((host, port), SimpleRESTHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    run()
