# AI News Bot

AI News Bot sends daily Telegram digests for two scheduled jobs:

- `research`: searches for recent research articles and papers on LLMs, agentic AI, computer vision, NLP, and machine learning.
- `news`: reads RSS feeds for recent news on defence, healthcare, fintech, sustainability, and politics.

The research job uses Tavily for search and the news job uses RSS feeds (via `feedparser`). Both use Groq for summarization with `openai/gpt-oss-120b` and the Telegram Bot API for delivery.

Each topic is handled by a dedicated agent. All agents run in parallel (fetch phase), while LLM summarization calls are serialized globally to respect the model's TPM rate limit. The final digest is compiled from all agents into a single Telegram message. If the message exceeds Telegram's 4096-character limit, it is split into chunks automatically.

The research digest is restricted to academic domains and uses a one-week search window. The news digest takes the newest articles from each topic's primary and fallback RSS feeds. Delivered URLs are stored in `state/seen_urls.json` so future runs skip already-seen articles.

---

## Architecture

The project follows a layered multi-agent architecture. Each layer has a single responsibility and can be changed independently.

```
main.py                          CLI entry point
│
├── config.py                    Centralized env vars and constants
│
├── orchestrator/
│   └── orchestrator.py          Runs agents in parallel, retries on failure,
│                                prints execution summary
│
├── agents/
│   ├── base_agent.py            Minimal abstract contract (name, knowledge key, execute)
│   ├── research/
│   │   ├── base_research_agent.py   Tavily lifecycle: search → filter → select → summarize
│   │   ├── llms_agent.py
│   │   ├── agentic_ai_agent.py
│   │   ├── computer_vision_agent.py
│   │   ├── nlp_agent.py
│   │   └── ml_agent.py
│   └── news/
│       ├── base_news_agent.py   RSS lifecycle: fetch → classify → rank → dedupe → summarize
│       ├── defence_agent.py
│       ├── healthcare_agent.py
│       ├── fintech_agent.py
│       ├── sustainability_agent.py
│       └── politics_agent.py
│
├── prompts/
│   ├── research/                One prompt file per research topic
│   └── news/                    One prompt file per news topic + classification_prompt.py
│
├── knowledge/
│   ├── knowledge_base.py        Loads domains.json, exposes retrieve(key)
│   └── domains.json             Research: domain allowlists + signals; News: RSS feeds + batch size
│
├── models/
│   ├── agent_response.py        AgentResponse, ArticleSummary, AgentExecutionResult
│   ├── feed_article.py          FeedArticle (title, url, published, content, geography)
│   └── digest_result.py         DigestResult
│
└── services/
    ├── llm_service.py           Groq wrapper — global semaphore for TPM safety
    ├── search_service.py        Tavily wrapper (research agents)
    ├── rss_service.py           feedparser wrapper — fetch(url, offset, count) (news agents)
    ├── article_classifier.py    Indian/Global classifier — pass-through skeleton for now
    ├── article_ranker.py        ArticleRanker ABC + ChronologicalRanker (newest first)
    ├── telegram_service.py      Telegram Bot API sender + message chunking
    └── url_tracker.py           seen_urls.json I/O + URL normalization
```

### Execution flow

Both jobs share the same orchestration; only the fetch step differs.

```
Config.validate(job_type)        TAVILY_API_KEY only required for `research`
       │
       ▼
Services created once per run
  research: LLMService + SearchService (Tavily) + KnowledgeBase
  news:     LLMService + RSSService + ArticleClassifier + ChronologicalRanker + KnowledgeBase
       │
       ▼
AgentOrchestrator — registers 5 agents, runs them in parallel (ThreadPoolExecutor)
       │
       ▼
Per agent (retry up to 3×):
  research: Tavily search → domain/abstract filter → dedupe → summarize
  news:     RSS primary + fallback feed → classify (no-op) → rank by date → dedupe → summarize
            ─── LLM calls serialized by global semaphore (5 s gap) ───
       │
       ▼
_compile_digest() → DigestResult
       │
  ┌────┴─────┐
  ▼          ▼
TelegramService   URLTracker
.send(message)    .mark_seen(urls)
```

### Agent design

Every agent inherits from `BaseAgent`, which defines three abstract members: `get_agent_name()`, `get_knowledge_key()` and `execute(max_results, seen_urls)`. The two tier base classes implement `execute()` themselves because the pipelines differ.

**Research agents** (`BaseResearchAgent`) additionally implement:

| Hook | Purpose |
|---|---|
| `get_search_query()` | Tavily query string |
| `build_summary_prompt(article)` | Topic-specific LLM prompt |

**News agents** (`BaseNewsAgent`) are constructed with `(llm, rss, classifier, ranker, kb)` and implement only `get_agent_name()`, `get_knowledge_key()` and `build_summary_prompt(article)`. Their feeds come from `domains.json`:

```json
"defence_news": {
  "feeds": { "primary": "<rss url>", "fallback": "<rss url>" },
  "batch_size": 2,
  "max_classify_retries": 3
}
```

### News pipeline extension points

- **Ranking** — `ArticleRanker` is an ABC. `ChronologicalRanker` sorts newest-first (undated last). Pass a different ranker in `main.py` to change ordering.
- **Classification** — `ArticleClassifier.classify()` is currently a pass-through. When implemented it should set `FeedArticle.geography` (`Indian` / `Global`). Then uncomment the two marked blocks in `agents/news/base_news_agent.py`: the geography filter and the retry loop that fetches further batches (`offset += batch_size`) until an Indian article is found or `max_classify_retries` is hit.

### Rate limit design

The model (`openai/gpt-oss-120b`) has a TPM limit of 8,000. A class-level `threading.Semaphore(1)` in `LLMService` ensures all LLM calls across all parallel agents are serialized, with a 5-second gap held inside the lock between calls. This prevents TPM bursts regardless of how many agents are running.

### Resilience

The orchestrator wraps each agent in a retry loop (up to 3 attempts, with 2 s / 4 s exponential back-off). A failed agent does not affect the others — its slot in the digest is simply omitted and its failure is printed in the execution summary.

---

## Requirements

- Python 3.11 or newer
- Tavily API key (research job only)
- Groq API key
- Telegram bot token
- Telegram chat ID

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Required
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key   # only needed for the research job
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Optional — defaults shown
MODEL_NAME=openai/gpt-oss-120b
MAX_RESULTS=1
AI_NEWS_BOT_LOG=ai-news-bot.log
```

`MAX_RESULTS` is the maximum number of articles **per topic agent**. With 5 agents, the digest contains at most `5 × MAX_RESULTS` articles. The default is 1 (up to 5 articles per digest).

---

## Local Setup

Clone the repo:

```bash
git clone https://github.com/Anhad-01/AI-news-bot.git
cd AI-news-bot
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Copy and fill in the environment file:

```bash
cp .env.example .env
```

Run the research digest:

```bash
python main.py research
```

Run the news digest:

```bash
python main.py news
```

**Test with minimal output** (1 article per agent, no Telegram):

```bash
python main.py research --max-results 1 --dry-run
python main.py news --max-results 1 --dry-run
```

**Send a small real digest** to Telegram:

```bash
python main.py research --max-results 1
python main.py news --max-results 1
```

---

## CLI Reference

```
python main.py <job_type> [--max-results N] [--dry-run]
```

| Argument | Description |
|---|---|
| `job_type` | `research` or `news` |
| `--max-results N` | Max articles per topic agent (5 agents × N = total max). Default: 3 |
| `--dry-run` | Print the digest to stdout instead of sending it to Telegram |

---

## GitHub Actions Setup

The bot runs on a schedule through GitHub Actions. Two workflows live in `.github/workflows/`:

| Workflow | File | Schedule (IST) |
|---|---|---|
| Daily News Digest | `news.yml` | Every day at 06:07 |
| AI Research Digest | `research.yml` | Monday and Thursday at 06:37 |

Both can also be started manually with `workflow_dispatch`.

### 1. Push the repo to GitHub

```bash
git push origin main
```

### 2. Add repository secrets

Go to **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Used by |
|---|---|
| `GROQ_API_KEY` | news, research |
| `TELEGRAM_BOT_TOKEN` | news, research |
| `TELEGRAM_CHAT_ID` | news, research |
| `TAVILY_API_KEY` | research only |

### 3. Allow the workflow to push state

The workflows commit `state/seen_urls.json` back to the repo after each run. Go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**.

### 4. Run a workflow manually

Open the **Actions** tab, choose a workflow, then click **Run workflow**. Confirm that the digest arrives in Telegram and that a commit named `Update seen URLs` appears.

### 5. Check logs

Each run uploads `ai-news-bot.log` as an artifact (kept for 30 days). Open the run page and download it from **Artifacts**. The step output also shows the per-agent execution summary.

### Changing the schedule

Edit the `cron` line in the workflow file. Times are interpreted in the zone given by `timezone` (`Asia/Kolkata`).

### Updating the bot

Push to `main`. The next scheduled run uses the new code and installs `requirements.txt` fresh each time, so there is nothing to update on a server.

---

## Extending the Bot

### Add a new topic agent

**Research:**
1. Add a prompt file in `prompts/research/`.
2. Add a domain entry in `knowledge/domains.json`.
3. Create an agent in `agents/research/` inheriting `BaseResearchAgent`; implement `get_agent_name()`, `get_knowledge_key()`, `get_search_query()` and `build_summary_prompt()`.
4. Add it to `_RESEARCH_AGENTS` in `main.py`.

**News:**
1. Add a prompt file in `prompts/news/`.
2. Add an entry in `knowledge/domains.json` with `feeds.primary`, `feeds.fallback`, `batch_size` and `max_classify_retries`.
3. Create an agent in `agents/news/` inheriting `BaseNewsAgent`; implement `get_agent_name()`, `get_knowledge_key()` and `build_summary_prompt(article)`.
4. Add it to `_NEWS_AGENTS` in `main.py`.

### Swap the LLM provider

Replace `services/llm_service.py` with a new wrapper that exposes the same `generate(prompt, temperature)` interface. Update `GROQ_API_KEY` and `MODEL_NAME` in `.env`. No agent or orchestrator code changes are needed.

### Swap the search provider (research)

Replace `services/search_service.py` with a wrapper exposing `search(query, **kwargs) -> list[dict[str, Any]]`. No agent code changes are needed.

### Swap the news source

Replace `services/rss_service.py` with a class exposing `fetch(url, offset, count) -> list[FeedArticle]`, or change feed URLs in `knowledge/domains.json`.
