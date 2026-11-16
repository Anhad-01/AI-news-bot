import threading
from datetime import datetime

from config import Config

_lock = threading.Lock()


def log_event(job_type: str, message: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} {job_type} {message}"
    with _lock:
        print(line, flush=True)
        try:
            with Config.LOG_PATH.open("a", encoding="utf-8") as f:
                f.write(f"{line}\n")
        except OSError:
            pass
