import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
    TAVILY_API_KEY: str | None = os.getenv("TAVILY_API_KEY")
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID: str | None = os.getenv("TELEGRAM_CHAT_ID")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "openai/gpt-oss-120b")

    # Tunable constants
    DEFAULT_MAX_RESULTS: int = int(os.getenv("MAX_RESULTS", "3"))
    MAX_CONTENT_CHARS: int = 12_000
    SEARCH_RESULTS_PER_TOPIC: int = 10
    SUMMARY_DELAY_SECONDS: float = 5.0
    TELEGRAM_MAX_CHARS: int = 4_096
    STATE_DIR: Path = Path("state")
    LOG_PATH: Path = Path(os.getenv("AI_NEWS_BOT_LOG", "ai-news-bot.log"))

    @staticmethod
    def validate() -> None:
        required = {
            "GROQ_API_KEY": Config.GROQ_API_KEY,
            "TAVILY_API_KEY": Config.TAVILY_API_KEY,
            "TELEGRAM_BOT_TOKEN": Config.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHAT_ID": Config.TELEGRAM_CHAT_ID,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
