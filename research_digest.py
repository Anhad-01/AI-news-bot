import re
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
SEARCH_RESULTS_PER_TOPIC = 10
RESEARCH_TOPICS = [
    "LLMs large language models",
    "agentic AI autonomous agents",
    "computer vision",
    "natural language processing NLP",
    "machine learning",
]
RESEARCH_DOMAINS = [
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "nature.com",
    "science.org",
    "sciencedirect.com",
    "elsevier.com",
    "springer.com",
    "aclanthology.org",
    "openreview.net",
    "ieee.org",
    "dl.acm.org",
    "jmlr.org",
    "proceedings.mlr.press",
    "biorxiv.org",
    "medrxiv.org",
]
STRONG_RESEARCH_DOMAINS = {
    "arxiv.org",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "openreview.net",
    "aclanthology.org",
    "jmlr.org",
    "proceedings.mlr.press",
    "biorxiv.org",
    "medrxiv.org",
}
RESEARCH_URL_SIGNALS = ("/abs/", "/pdf/", "/article/", "/paper/", "/content/", "/doi/")
RESEARCH_TEXT_SIGNALS = ("abstract", "doi", "journal", "conference", "preprint")


def search_topic(client: TavilyClient, topic: str) -> list[dict]:
    query = f"latest research articles papers from the past week about {topic}"
    response = client.search(
        query=query,
        topic="general",
        time_range="week",
        include_domains=RESEARCH_DOMAINS,
        max_results=SEARCH_RESULTS_PER_TOPIC,
        include_raw_content=True,
        search_depth="basic",
    )
    return response.get("results", [])


def is_allowed_research_domain(domain: str) -> bool:
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in RESEARCH_DOMAINS)


def has_research_signal(article: dict, normalized: str, domain: str) -> bool:
    if domain in STRONG_RESEARCH_DOMAINS:
        return True

    content = article.get("raw_content") or article.get("content") or ""
    text = f"{article.get('title', '')} {content}".lower()
    url_path = normalized.lower()

    return any(signal in url_path for signal in RESEARCH_URL_SIGNALS) or any(
        signal in text for signal in RESEARCH_TEXT_SIGNALS
    )


def extract_abstract(article: dict) -> str:
    content = article.get("raw_content") or article.get("content") or ""
    if not content:
        return ""

    collapsed = re.sub(r"\s+", " ", content).strip()
    match = re.search(
        r"\babstract\b[:\s-]*(.*?)(?:\bintroduction\b|\bbackground\b|\bkeywords\b|\breferences\b|$)",
        collapsed,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""

    abstract = match.group(1).strip()
    return abstract[:5000]


def summarize_research_article(client: Groq, article: dict) -> str:
    title = article.get("title") or "Untitled"
    url = article.get("url") or ""
    abstract = extract_abstract(article)
    content = article.get("raw_content") or article.get("content") or ""
    source_text = abstract or content[:MAX_CONTENT_CHARS] or title
    source_label = "Abstract" if abstract else "Article text"

    prompt = (
        "Summarize this research article in 2-3 concise sentences. "
        "Focus on the research contribution, method or dataset if available, and key finding. "
        "Only use information supported by the provided text. Do not use an introductory phrase.\n\n"
        f"Title: {title}\n"
        f"URL: {url}\n"
        f"{source_label}:\n{source_text}"
    )
    completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name(),
        temperature=0.3,
    )
    return completion.choices[0].message.content.strip()


def build_research_digest(max_results: int) -> DigestResult:
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
        "skipped_filter": 0,
        "skipped_domain": 0,
    }

    for topic in RESEARCH_TOPICS:
        for article in search_topic(tavily_client, topic):
            stats["found"] += 1
            url = normalized_url(article.get("url", ""))
            domain = domain_for_url(url)
            if not url or url in seen_urls or url in run_urls:
                stats["skipped_seen"] += 1
                continue
            if not is_allowed_research_domain(domain) or not has_research_signal(article, url, domain):
                stats["skipped_filter"] += 1
                continue
            if domain_counts[domain] >= 1:
                stats["skipped_domain"] += 1
                continue

            selected.append((topic, article, url, domain))
            run_urls.add(url)
            domain_counts[domain] += 1
            if len(selected) >= max_results:
                break
        if len(selected) >= max_results:
            break

    if not selected:
        message = format_digest("Daily AI Research Digest", ["No matching research articles found."])
        return DigestResult(message=message, urls=[], stats=stats)

    items = []
    delivered_urls = []
    for idx, (topic, article, url, _domain) in enumerate(selected, start=1):
        title = article.get("title") or "Untitled"
        try:
            summary = summarize_research_article(groq_client, article)
        except Exception as exc:
            summary = f"Summary failed: {exc}"

        items.append(f"{idx}. {title}\nTopic: {topic}\nSummary: {summary}\nSource: {url}")
        delivered_urls.append(url)

        if idx < len(selected):
            time.sleep(SUMMARY_DELAY_SECONDS)

    stats["sent"] = len(delivered_urls)
    return DigestResult(
        message=format_digest("Daily AI Research Digest", items),
        urls=delivered_urls,
        stats=stats,
    )
