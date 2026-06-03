import argparse
import sys

from digest_common import (
    DEFAULT_MAX_RESULTS,
    load_environment,
    log_event,
    mark_seen_urls,
    required_env,
    send_to_telegram,
)


def build_digest(job_type: str, max_results: int):
    if job_type == "research":
        from research_digest import build_research_digest

        return build_research_digest(max_results)
    if job_type == "news":
        from news_digest import build_news_digest

        return build_news_digest(max_results)
    raise ValueError("job_type must be either 'research' or 'news'")


def run_job(job_type: str, max_results: int = DEFAULT_MAX_RESULTS, dry_run: bool = False) -> str:
    load_environment()
    log_event(job_type, "start")

    digest = build_digest(job_type, max_results=max_results)
    if dry_run:
        print(digest.message)
        log_event(job_type, f"dry-run found={digest.stats.get('found', 0)} sent={digest.stats.get('sent', 0)}")
        return digest.message

    send_to_telegram(
        bot_token=required_env("TELEGRAM_BOT_TOKEN"),
        chat_id=required_env("TELEGRAM_CHAT_ID"),
        message=digest.message,
    )
    mark_seen_urls(digest.urls)

    log_event(
        job_type,
        "done "
        f"found={digest.stats.get('found', 0)} "
        f"sent={digest.stats.get('sent', 0)} "
        f"seen={digest.stats.get('skipped_seen', 0)} "
        f"filter={digest.stats.get('skipped_filter', 0)} "
        f"domain={digest.stats.get('skipped_domain', 0)}",
    )
    return digest.message


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
