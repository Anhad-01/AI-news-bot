# AI News Bot

AI News Bot sends daily Telegram digests for two scheduled jobs:

- `research`: searches for recent research articles and papers on LLMs, agentic AI, computer vision, NLP, and machine learning.
- `news`: searches for recent news articles on defence, healthcare, fintech, sustainable development, climate, and politics.

The bot uses Tavily for search, Groq for article summarization with `meta-llama/llama-4-scout-17b-16e-instruct`, and Telegram Bot API for delivery.

Each article is summarized individually with a short delay between summaries. The final digest is sent as one Telegram message when possible. If the message exceeds Telegram's size limit, it is split into multiple chunks.

The research digest is limited to research-oriented domains and uses a one-week search window. The news digest uses a one-day search window. Delivered URLs are stored locally in `state/seen_urls.json` so future cron runs skip repeats.

## Code Layout

- `main.py`: CLI router used by cron.
- `research_digest.py`: AI research search, filtering, and summarization.
- `news_digest.py`: daily news search, filtering, and summarization.
- `digest_common.py`: shared environment, Telegram, logging, and URL-history helpers.

## Requirements

- Python 3.11 or newer
- Tavily API key
- Groq API key
- Telegram bot token
- Telegram chat ID

## Environment Variables

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=your_tavily_api_key
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct
```

`MODEL_NAME` is optional. If omitted, the app uses `meta-llama/llama-4-scout-17b-16e-instruct`.

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

Create `.env` using the format above.

Run the research digest:

```bash
python main.py research
```

Run the news digest:

```bash
python main.py news
```

For a smaller test run:

```bash
python main.py research --max-results 1
python main.py news --max-results 1
```

To build and print the digest without sending it to Telegram:

```bash
python main.py research --dry-run
python main.py news --dry-run
```

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
nano /opt/AI-news-bot/.env
```

Add:

```env
TAVILY_API_KEY=your_tavily_api_key
GROQ_API_KEY=your_groq_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
MODEL_NAME=meta-llama/llama-4-scout-17b-16e-instruct
```

Restrict permissions:

```bash
chmod 600 /opt/AI-news-bot/.env
```

Test manually:

```bash
cd /opt/AI-news-bot
.venv/bin/python main.py research --max-results 1
.venv/bin/python main.py news --max-results 1
```

## Cron Setup

The intended schedule is:

- Research digest: every day at 9:00 AM IST
- News digest: every day at 9:30 AM IST

If the server timezone is `Asia/Kolkata`, edit root's crontab:

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

## Updating the Server

After pushing changes to GitHub:

```bash
cd /opt/AI-news-bot
git pull origin main
.venv/bin/pip install -r requirements.txt
```

Run a quick test:

```bash
.venv/bin/python main.py research --max-results 1
```
