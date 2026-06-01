import argparse
import os
import sys
import time
from datetime import datetime
from typing import Iterable

import requests
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient


DEFAULT_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
DEFAULT_MAX_RESULTS = 5
SUMMARY_DELAY_SECONDS = 5
MAX_CONTENT_CHARS = 12000
TELEGRAM_MAX_CHARS = 4096

RESEARCH_QUERY = (
    "latest research articles papers on LLMs OR large language models, "
    "agentic AI, computer vision, NLP, machine learning"
)
NEWS_QUERY = (
    "latest news articles on defence, healthcare, fintech, sustainable "
    "development, climate, politics"
)


def required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_search_results(
    client: TavilyClient,
    query: str,
    topic_type: str,
    max_results: int = DEFAULT_MAX_RESULTS,
) -> list[dict]:
    response = client.search(
        query=query,
        topic=topic_type,
        max_results=max_results,
        include_raw_content=True,
        search_depth="advanced",
    )
    return response.get("results", [])


def summarize_with_groq(client: Groq, model_name: str, article: dict) -> str:
    title = article.get("title", "Untitled")
    url = article.get("url", "")
    content = article.get("raw_content") or article.get("content") or ""
    text_to_summarize = content[:MAX_CONTENT_CHARS] if content else title

    prompt = (
        "Summarize this article individually in 2-3 concise sentences. "
        "Focus on the concrete finding, announcement, policy change, or market impact. "
        "Do not use an introductory phrase. If the text is thin, summarize only what can "
        "be supported by the title and source URL.\n\n"
        f"Title: {title}\n"
        f"URL: {url}\n"
        f"Article text:\n{text_to_summarize}"
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
        temperature=0.3,
    )
    return chat_completion.choices[0].message.content.strip()


def format_digest(title: str, current_date: str, items: Iterable[str]) -> str:
    body = f"{title} [{current_date}]\n\n"
    return body + "\n\n".join(items)


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


def build_digest(job_type: str, max_results: int = DEFAULT_MAX_RESULTS) -> str:
    load_dotenv()

    tavily_client = TavilyClient(api_key=required_env("TAVILY_API_KEY"))
    groq_client = Groq(api_key=required_env("GROQ_API_KEY"))
    model_name = os.getenv("MODEL_NAME", DEFAULT_MODEL)
    current_date = datetime.now().strftime("%B %d, %Y")

    if job_type == "research":
        query = RESEARCH_QUERY
        topic = "general"
        digest_title = "Daily AI Research Digest"
    elif job_type == "news":
        query = NEWS_QUERY
        topic = "news"
        digest_title = "Daily News Digest"
    else:
        raise ValueError("job_type must be either 'research' or 'news'")

    results = get_search_results(tavily_client, query, topic, max_results=max_results)
    if not results:
        return format_digest(digest_title, current_date, ["No matching articles found."])

    items = []
    for idx, article in enumerate(results, start=1):
        title = article.get("title") or "Untitled"
        url = article.get("url") or "No URL"
        try:
            summary = summarize_with_groq(groq_client, model_name, article)
        except Exception as exc:
            summary = f"Summary failed: {exc}"

        items.append(f"{idx}. {title}\nSummary: {summary}\nSource: {url}")

        if idx < len(results):
            time.sleep(SUMMARY_DELAY_SECONDS)

    return format_digest(digest_title, current_date, items)


def run_job(job_type: str, max_results: int = DEFAULT_MAX_RESULTS, dry_run: bool = False) -> str:
    load_dotenv()

    message = build_digest(job_type, max_results=max_results)
    if dry_run:
        print(message)
        return message

    send_to_telegram(
        bot_token=required_env("TELEGRAM_BOT_TOKEN"),
        chat_id=required_env("TELEGRAM_CHAT_ID"),
        message=message,
    )
    return message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send AI research or news digests to Telegram.")
    parser.add_argument("job_type", choices=["research", "news"])
    parser.add_argument("--max-results", type=int, default=DEFAULT_MAX_RESULTS)
    parser.add_argument("--dry-run", action="store_true", help="Print the digest instead of sending it.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_job(args.job_type, max_results=args.max_results, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Job failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
