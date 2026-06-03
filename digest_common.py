import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from dotenv import load_dotenv


DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEFAULT_MAX_RESULTS = 5
SUMMARY_DELAY_SECONDS = 5
TELEGRAM_MAX_CHARS = 4096
STATE_DIR = Path("state")
SEEN_URLS_PATH = STATE_DIR / "seen_urls.json"
LOG_PATH = Path(os.getenv("AI_NEWS_BOT_LOG", "ai-news-bot.log"))
TRACKING_PARAMS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid", "ref"}


@dataclass
class DigestResult:
    message: str
    urls: list[str]
    stats: dict[str, int] = field(default_factory=dict)


def load_environment() -> None:
    load_dotenv()


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def model_name() -> str:
    return os.getenv("MODEL_NAME", DEFAULT_MODEL)


def timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def log_event(job_type: str, message: str) -> None:
    line = f"{timestamp()} {job_type} {message}"
    print(line, flush=True)
    try:
        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(f"{line}\n")
    except OSError:
        pass


def format_digest(title: str, items: Iterable[str]) -> str:
    current_date = datetime.now().strftime("%B %d, %Y")
    return f"{title} [{current_date}]\n\n" + "\n\n".join(items)


def normalized_url(url: str) -> str:
    if not url:
        return ""

    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower() or "https"
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    query_items = []

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key.startswith("utm_") or lower_key in TRACKING_PARAMS:
            continue
        query_items.append((key, value))

    return urlunsplit((scheme, netloc, path, urlencode(query_items), ""))


def domain_for_url(url: str) -> str:
    netloc = urlsplit(url).netloc.lower()
    if netloc.startswith("www."):
        return netloc[4:]
    return netloc


def load_seen_urls() -> set[str]:
    if not SEEN_URLS_PATH.exists():
        return set()

    try:
        data = json.loads(SEEN_URLS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()

    if isinstance(data, list):
        return set(item for item in data if isinstance(item, str))
    return set()


def save_seen_urls(urls: set[str]) -> None:
    STATE_DIR.mkdir(exist_ok=True)
    SEEN_URLS_PATH.write_text(
        json.dumps(sorted(urls), indent=2),
        encoding="utf-8",
    )


def mark_seen_urls(new_urls: Iterable[str]) -> None:
    seen_urls = load_seen_urls()
    seen_urls.update(url for url in new_urls if url)
    save_seen_urls(seen_urls)


def split_telegram_message(message: str) -> list[str]:
    if len(message) <= TELEGRAM_MAX_CHARS:
        return [message]

    chunks = []
    current = ""
    for block in message.split("\n\n"):
        candidate = f"{current}\n\n{block}".strip() if current else block
        if len(candidate) <= TELEGRAM_MAX_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
        current = block[:TELEGRAM_MAX_CHARS]
    if current:
        chunks.append(current)
    return chunks


def send_to_telegram(bot_token: str, chat_id: str, message: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = split_telegram_message(message)
    for idx, chunk in enumerate(chunks, start=1):
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": chunk,
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        response.raise_for_status()
        if idx < len(chunks):
            time.sleep(1)
