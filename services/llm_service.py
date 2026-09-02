import threading
import time

from groq import Groq


class LLMService:
    # Class-level semaphore: enforces serial LLM calls across all agents
    # regardless of thread count. This is the primary TPM guard.
    _lock: threading.Semaphore = threading.Semaphore(1)

    def __init__(self, api_key: str, model: str, delay: float = 5.0) -> None:
        self._client = Groq(api_key=api_key)
        self._model = model
        self._delay = delay

    def generate(self, prompt: str, temperature: float = 0.3) -> str:
        with self._lock:
            completion = self._client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self._model,
                temperature=temperature,
            )
            result = completion.choices[0].message.content.strip()
            # Hold the lock through the delay to space out calls globally.
            time.sleep(self._delay)
            return result
