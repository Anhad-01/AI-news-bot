import time
from collections import Counter

from groq import Groq
from tavily import TavilyClient

from digest_common import (
    DigestResult,
    SUMMARY_DELAY_SECONDS,
    domain_for_url,
    format_digest,
    load_seen_urls,
    model_name,
    normalized_url,
    required_env,
)


MAX_CONTENT_CHARS = 12000
NEWS_QUERY = (
    "latest news articles from today on defence, healthcare, fintech, "
    "sustainable development, climate, politics"
)


def search_news(client: TavilyClient, max_results: int) -> list[dict]:
    response = client.search(
        query=NEWS_QUERY,
        topic="news",
        time_range="day",
        days=1,
        max_results=max(max_results * 3, 10),
        include_raw_content=True,
        search_depth="basic",
    )
    return response.get("results", [])


def summarize_news_article(client: Groq, article: dict) -> str:
    title = article.get("title") or "Untitled"
    url = article.get("url") or ""
    content = article.get("raw_content") or article.get("content") or title

    prompt = (
        "Summarize this news article in 2-3 concise sentences. "
        "Use only the article body and ignore navigation text, ads, related links, captions, "
        "and boilerplate. Focus on what happened, who is affected, and why it matters. "
        "Do not use an introductory phrase.\n\n"
        f"Title: {title}\n"
        f"URL: {url}\n"
        f"Article text:\n{content[:MAX_CONTENT_CHARS]}"
    )
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name(),
        temperature=0.3,
    )
    return completion.choices[0].message.content.strip()


def build_news_digest(max_results: int) -> DigestResult:
    tavily_client = TavilyClient(api_key=required_env("TAVILY_API_KEY"))
    groq_client = Groq(api_key=required_env("GROQ_API_KEY"))
    seen_urls = load_seen_urls()
    run_urls = set()
    domain_counts: Counter[str] = Counter()
    selected = []
    stats = {
        "found": 0,
        "sent": 0,
        "skipped_seen": 0,
        "skipped_domain": 0,
    }

    for article in search_news(tavily_client, max_results):
        stats["found"] += 1
        url = normalized_url(article.get("url", ""))
        domain = domain_for_url(url)
        if not url or url in seen_urls or url in run_urls:
            stats["skipped_seen"] += 1
            continue
        if domain_counts[domain] >= 1:
            stats["skipped_domain"] += 1
            continue

        selected.append((article, url, domain))
        run_urls.add(url)
        domain_counts[domain] += 1
        if len(selected) >= max_results:
            break

    if not selected:
        message = format_digest("Daily News Digest", ["No matching news articles found."])
        return DigestResult(message=message, urls=[], stats=stats)

    items = []
    delivered_urls = []
    for idx, (article, url, _domain) in enumerate(selected, start=1):
        title = article.get("title") or "Untitled"
        try:
            summary = summarize_news_article(groq_client, article)
        except Exception as exc:
            summary = f"Summary failed: {exc}"

        items.append(f"{idx}. {title}\nSummary: {summary}\nSource: {url}")
        delivered_urls.append(url)

        if idx < len(selected):
            time.sleep(SUMMARY_DELAY_SECONDS)

    stats["sent"] = len(delivered_urls)
    return DigestResult(
        message=format_digest("Daily News Digest", items),
        urls=delivered_urls,
        stats=stats,
    )
