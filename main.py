import argparse
import sys
from datetime import datetime

from agents.news.defence_agent import DefenceNewsAgent
from agents.news.fintech_agent import FintechNewsAgent
from agents.news.healthcare_agent import HealthcareNewsAgent
from agents.news.politics_agent import PoliticsNewsAgent
from agents.news.sustainability_agent import SustainabilityNewsAgent
from agents.research.agentic_ai_agent import AgenticAIResearchAgent
from agents.research.computer_vision_agent import ComputerVisionResearchAgent
from agents.research.llms_agent import LLMsResearchAgent
from agents.research.ml_agent import MLResearchAgent
from agents.research.nlp_agent import NLPResearchAgent
from config import Config
from knowledge.knowledge_base import KnowledgeBase
from models.agent_response import AgentResponse
from models.digest_result import DigestResult
from orchestrator.orchestrator import AgentOrchestrator
from services.llm_service import LLMService
from services.search_service import SearchService
from services.telegram_service import TelegramService
from services.url_tracker import URLTracker

_RESEARCH_AGENTS = [
    LLMsResearchAgent,
    AgenticAIResearchAgent,
    ComputerVisionResearchAgent,
    NLPResearchAgent,
    MLResearchAgent,
]

_NEWS_AGENTS = [
    DefenceNewsAgent,
    HealthcareNewsAgent,
    FintechNewsAgent,
    SustainabilityNewsAgent,
    PoliticsNewsAgent,
]


def log_event(job_type: str, message: str) -> None:
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M')} {job_type} {message}"
    print(line, flush=True)
    try:
        with Config.LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"{line}\n")
    except OSError:
        pass


def _make_services() -> tuple[LLMService, SearchService, KnowledgeBase]:
    # Both keys are guaranteed non-None after Config.validate() in run_job().
    groq_key = Config.GROQ_API_KEY or ""
    tavily_key = Config.TAVILY_API_KEY or ""
    llm = LLMService(
        api_key=groq_key,
        model=Config.MODEL_NAME,
        delay=Config.SUMMARY_DELAY_SECONDS,
    )
    search = SearchService(api_key=tavily_key)
    kb = KnowledgeBase()
    return llm, search, kb


def _compile_digest(title: str, responses: list[AgentResponse]) -> DigestResult:
    """Merge all agent responses into a single DigestResult."""
    current_date = datetime.now().strftime("%B %d, %Y")
    items: list[str] = []
    all_urls: list[str] = []
    stats = {"found": 0, "sent": 0, "failed_agents": 0}

    for response in sorted(responses, key=lambda r: r.agent_name):
        if not response.is_success() or not response.articles:
            stats["failed_agents"] += 1
            continue
        for article in response.articles:
            stats["found"] += 1
            items.append(
                f"{len(items) + 1}. {article.title}\n"
                f"Topic: {article.topic}\n"
                f"Summary: {article.summary}\n"
                f"Source: {article.url}"
            )
            all_urls.append(article.url)
            stats["sent"] += 1

    body = "\n\n".join(items) if items else "No articles found."
    message = f"{title} [{current_date}]\n\n{body}"
    return DigestResult(message=message, urls=all_urls, stats=stats)


def build_research_digest(max_results: int) -> DigestResult:
    llm, search, kb = _make_services()
    orchestrator = AgentOrchestrator()
    for agent_cls in _RESEARCH_AGENTS:
        orchestrator.register(agent_cls(llm, search, kb))

    seen_urls = URLTracker(Config.STATE_DIR).load()
    responses = orchestrator.execute_all(max_results, seen_urls)
    orchestrator.display_execution_summary()
    return _compile_digest("Daily AI Research Digest", responses)


def build_news_digest(max_results: int) -> DigestResult:
    llm, search, kb = _make_services()
    orchestrator = AgentOrchestrator()
    for agent_cls in _NEWS_AGENTS:
        orchestrator.register(agent_cls(llm, search, kb))

    seen_urls = URLTracker(Config.STATE_DIR).load()
    responses = orchestrator.execute_all(max_results, seen_urls)
    orchestrator.display_execution_summary()
    return _compile_digest("Daily News Digest", responses)


def run_job(
    job_type: str,
    max_results: int = Config.DEFAULT_MAX_RESULTS,
    dry_run: bool = False,
) -> str:
    Config.validate()
    log_event(job_type, "start")

    if job_type == "research":
        digest = build_research_digest(max_results)
    elif job_type == "news":
        digest = build_news_digest(max_results)
    else:
        raise ValueError("job_type must be 'research' or 'news'")

    if dry_run:
        print(digest.message)
        log_event(
            job_type,
            f"dry-run found={digest.stats.get('found', 0)} sent={digest.stats.get('sent', 0)}",
        )
        return digest.message

    # Both values are guaranteed non-None after Config.validate().
    telegram = TelegramService(
        bot_token=Config.TELEGRAM_BOT_TOKEN or "",
        chat_id=Config.TELEGRAM_CHAT_ID or "",
    )
    telegram.send(digest.message)
    URLTracker(Config.STATE_DIR).mark_seen(digest.urls)

    log_event(
        job_type,
        f"done "
        f"found={digest.stats.get('found', 0)} "
        f"sent={digest.stats.get('sent', 0)} "
        f"failed_agents={digest.stats.get('failed_agents', 0)}",
    )
    return digest.message


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send AI research or news digests to Telegram."
    )
    parser.add_argument("job_type", choices=["research", "news"])
    parser.add_argument(
        "--max-results",
        type=int,
        default=Config.DEFAULT_MAX_RESULTS,
        help="Max articles per topic agent (5 agents x N = total max articles). Default: %(default)s.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the digest to stdout instead of sending it to Telegram.",
    )
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
