import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from agents.base_agent import BaseAgent
from models.agent_response import AgentExecutionResult, AgentResponse, AgentStatus


class AgentOrchestrator:
    """
    Execution engine for a set of registered agents.

    Responsibilities:
    - Run all agents in parallel via ThreadPoolExecutor (search phase).
    - Retry each agent up to MAX_RETRIES times with exponential back-off.
    - Track per-agent execution results for the summary display.
    """

    MAX_RETRIES = 3

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        self._execution_results: list[AgentExecutionResult] = []
        self._results_lock = threading.Lock()

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.get_agent_name()] = agent

    def execute_all(self, max_results: int, seen_urls: set[str]) -> list[AgentResponse]:
        """Run all registered agents in parallel; collect and return their responses."""
        with ThreadPoolExecutor(max_workers=len(self._agents)) as pool:
            futures = {
                pool.submit(self._execute_with_retry, agent, max_results, seen_urls): name
                for name, agent in self._agents.items()
            }
            return [future.result() for future in as_completed(futures)]

    def display_execution_summary(self) -> None:
        print("\n── Execution Summary " + "─" * 48)
        for result in sorted(self._execution_results, key=lambda r: r.agent_name):
            icon = "✓" if result.status == AgentStatus.SUCCESS else "✗"
            line = (
                f"  {icon} {result.agent_name:<35}"
                f"  attempts={result.attempts}"
                f"  time={result.execution_time:.1f}s"
            )
            if result.error_message:
                line += f"  error={result.error_message}"
            print(line)
        print("─" * 68 + "\n")

    # ── private ──────────────────────────────────────────────────────────────

    def _execute_with_retry(
        self,
        agent: BaseAgent,
        max_results: int,
        seen_urls: set[str],
    ) -> AgentResponse:
        last_exc: Exception | None = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            t0 = time.monotonic()
            try:
                response = agent.execute(max_results, seen_urls)
                elapsed = time.monotonic() - t0
                self._record(AgentExecutionResult(
                    agent_name=agent.get_agent_name(),
                    status=AgentStatus.SUCCESS,
                    attempts=attempt,
                    execution_time=elapsed,
                ))
                return response
            except Exception as exc:
                last_exc = exc
                elapsed = time.monotonic() - t0
                if attempt == self.MAX_RETRIES:
                    self._record(AgentExecutionResult(
                        agent_name=agent.get_agent_name(),
                        status=AgentStatus.FAILED,
                        attempts=attempt,
                        execution_time=elapsed,
                        error_message=str(exc),
                    ))
                else:
                    # Exponential back-off before next attempt (2 s, 4 s).
                    time.sleep(2 ** attempt)

        return AgentResponse(
            agent_name=agent.get_agent_name(),
            articles=[],
            status=AgentStatus.FAILED,
            error=str(last_exc),
        )

    def _record(self, result: AgentExecutionResult) -> None:
        with self._results_lock:
            self._execution_results.append(result)
