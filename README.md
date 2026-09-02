# AI News Bot

AI News Bot sends daily Telegram digests for two scheduled jobs:

- `research`: searches for recent research articles and papers on LLMs, agentic AI, computer vision, NLP, and machine learning.
- `news`: searches for recent news articles on defence, healthcare, fintech, sustainable development, climate, and politics.

The bot uses Tavily for search, Groq for article summarization with `openai/gpt-oss-120b`, and the Telegram Bot API for delivery.

Each topic is handled by a dedicated agent. All agents run in parallel (search phase), while LLM summarization calls are serialized globally to respect the model's TPM rate limit. The final digest is compiled from all agents into a single Telegram message. If the message exceeds Telegram's 4096-character limit, it is split into chunks automatically.

The research digest is restricted to academic domains and uses a one-week search window. The news digest uses a one-day search window. Delivered URLs are stored in `state/seen_urls.json` so future runs skip already-seen articles.

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
│   ├── base_agent.py            Abstract base — owns the execute() lifecycle
│   ├── research/
│   │   ├── base_research_agent.py   Shared academic filtering + abstract extraction
│   │   ├── llms_agent.py
│   │   ├── agentic_ai_agent.py
│   │   ├── computer_vision_agent.py
│   │   ├── nlp_agent.py
│   │   └── ml_agent.py
│   └── news/
│       ├── base_news_agent.py   Shared news search params
│       ├── defence_agent.py
│       ├── healthcare_agent.py
│       ├── fintech_agent.py
│       ├── sustainability_agent.py
│       └── politics_agent.py
│
├── prompts/
│   ├── research/                One prompt file per research topic
│   └── news/                    One prompt file per news topic
│
├── knowledge/
│   ├── knowledge_base.py        Loads domains.json, exposes retrieve(key)
│   └── domains.json             Per-agent domain allowlists and filter signals
│
├── models/
│   ├── agent_response.py        AgentResponse, ArticleSummary, AgentExecutionResult
│   └── digest_result.py         DigestResult
│
└── services/
    ├── llm_service.py           Groq wrapper — global semaphore for TPM safety
    ├── search_service.py        Tavily wrapper
    ├── telegram_service.py      Telegram Bot API sender + message chunking
    └── url_tracker.py           seen_urls.json I/O + URL normalization
```

### Execution flow

```
Config.validate()
       │
       ▼
LLMService + SearchService + KnowledgeBase   (created once per run)
       │
       ▼
AgentOrchestrator
  registers 5 agents
       │
       ▼
ThreadPoolExecutor — all 5 agents run in parallel
  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐
  │ Agent 1    │  │ Agent 2    │  │ Agent 3    │  │ Agent 4    │  │ Agent 5    │
  │ search()   │  │ search()   │  │ search()   │  │ search()   │  │ search()   │
  │ filter()   │  │ filter()   │  │ filter()   │  │ filter()   │  │ filter()   │
  │ ──────── serialized LLM calls (global semaphore, 5 s gap) ──────────────── │
  │ summarize()│  │ summarize()│  │ summarize()│  │ summarize()│  │ summarize()│
  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
        └───────────────┴───────────────┴───────────────┴───────────────┘
                                         │
                                         ▼
                              compile_digest()  →  DigestResult
                                         │
                              ┌──────────┴──────────┐
                              ▼                     ▼
                       TelegramService         URLTracker
                        .send(message)        .mark_seen(urls)
```

### Agent design

Every agent inherits from `BaseAgent` and implements four hooks:

| Hook | Purpose |
|---|---|
| `get_agent_name()` | Human-readable label used in the digest and execution summary |
| `get_knowledge_key()` | Key into `domains.json` for this agent's domain config |
| `get_search_query()` | Tavily query string |
| `build_summary_prompt(article)` | Formats the topic-specific LLM prompt |

`BaseAgent.execute()` owns the full lifecycle and is never overridden:

```
search() → filter() → select() → summarize() → AgentResponse
```

`BaseResearchAgent` and `BaseNewsAgent` fill in `get_search_params()` and `filter_article()` with their shared logic. The 10 concrete agents each implement only the four hooks above.

### Rate limit design

The model (`openai/gpt-oss-120b`) has a TPM limit of 8,000. A class-level `threading.Semaphore(1)` in `LLMService` ensures all LLM calls across all parallel agents are serialized, with a 5-second gap held inside the lock between calls. This prevents TPM bursts regardless of how many agents are running.

### Resilience

The orchestrator wraps each agent in a retry loop (up to 3 attempts, with 2 s / 4 s exponential back-off). A failed agent does not affect the others — its slot in the digest is simply omitted and its failure is printed in the execution summary.

---

## Requirements

- Python 3.11 or newer
- Tavily API key
- Groq API key
- Telegram bot token
- Telegram chat ID

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```env
# Required
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
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

## Remote Server Setup

These instructions assume an Ubuntu server and deployment under `/opt/AI-news-bot`.

Update the server and set the timezone:

```bash
sudo apt update
sudo apt upgrade
sudo timedatectl set-timezone Asia/Kolkata
```

Install required system packages if needed:

```bash
sudo apt install -y git python3 python3-venv
```

Clone the repo:

```bash
cd /opt
git clone https://github.com/Anhad-01/AI-news-bot.git AI-news-bot
cd /opt/AI-news-bot
```

If the repo already exists, pull the latest code instead:

```bash
cd /opt/AI-news-bot
git pull origin main
```

Create the virtual environment and install dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

Create the server `.env`:

```bash
cp .env.example .env
nano .env
```

Restrict permissions:

```bash
chmod 600 /opt/AI-news-bot/.env
```

Test manually:

```bash
cd /opt/AI-news-bot
.venv/bin/python main.py research --max-results 1 --dry-run
.venv/bin/python main.py news --max-results 1 --dry-run
```

---

## Cron Setup

The intended schedule is:

- Research digest: every day at 9:00 AM IST
- News digest: every day at 9:30 AM IST

If the server timezone is `Asia/Kolkata`, edit the crontab:

```bash
crontab -e
```

Add:

```cron
0 9 * * * cd /opt/AI-news-bot && .venv/bin/python main.py research >> /var/log/ai-news-bot.log 2>&1
30 9 * * * cd /opt/AI-news-bot && .venv/bin/python main.py news >> /var/log/ai-news-bot.log 2>&1
```

Verify:

```bash
crontab -l
systemctl status cron
```

Check logs:

```bash
tail -n 100 /var/log/ai-news-bot.log
```

If the server timezone is UTC, use these cron times instead:

```cron
30 3 * * * cd /opt/AI-news-bot && .venv/bin/python main.py research >> /var/log/ai-news-bot.log 2>&1
0 4 * * * cd /opt/AI-news-bot && .venv/bin/python main.py news >> /var/log/ai-news-bot.log 2>&1
```

---

## Updating the Server

After pushing changes to GitHub:

```bash
cd /opt/AI-news-bot
git pull origin main
.venv/bin/pip install -r requirements.txt
```

Test before the next cron run:

```bash
.venv/bin/python main.py research --max-results 1 --dry-run
```

---

## Extending the Bot

### Add a new topic agent

1. Add a prompt file in `prompts/news/` or `prompts/research/`.
2. Add a domain config entry in `knowledge/domains.json` under the new agent's key.
3. Create an agent file in `agents/news/` or `agents/research/` inheriting `BaseNewsAgent` or `BaseResearchAgent`. Implement `get_agent_name()`, `get_knowledge_key()`, `get_search_query()`, and `build_summary_prompt()`.
4. Add the new agent class to `_NEWS_AGENTS` or `_RESEARCH_AGENTS` in `main.py`.

Nothing else needs to change.

### Swap the LLM provider

Replace `services/llm_service.py` with a new wrapper that exposes the same `generate(prompt, temperature)` interface. Update `GROQ_API_KEY` and `MODEL_NAME` in `.env`. No agent or orchestrator code changes are needed.

### Swap the search provider

Replace `services/search_service.py` with a wrapper exposing `search(query, **kwargs) -> list[dict[str, Any]]`. No agent code changes are needed.
