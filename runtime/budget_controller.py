"""
AgentOps Nexus — Centralized Budget Controller & Circuit Breaker

Replaces per-module limits with a single authoritative RunBudgetController.
Enforces hard limits on tokens, cost, time, file changes, and iterations.
When any threshold is breached, the circuit breaker fires and halts the pipeline.
"""
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class BudgetLimits:
    """Configurable limits for a single execution run."""
    max_tokens: int = 500000
    max_cost_usd: float = 5.00
    max_seconds: int = 600
    max_files_modified: int = 10
    max_lines_changed: int = 500
    max_patch_iterations: int = 3


@dataclass
class BudgetUsage:
    """Current usage counters. Thread-safe via the controller's lock."""
    tokens_used: int = 0
    cost_usd: float = 0.0
    files_modified: int = 0
    lines_changed: int = 0
    patch_iterations: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time


class BudgetExhaustedError(Exception):
    """Raised when a budget limit is breached. Contains structured report."""
    def __init__(self, category: str, current: float, limit: float, message: str):
        self.category = category
        self.current = current
        self.limit = limit
        self.report = {
            "category": category,
            "current_value": current,
            "limit_value": limit,
            "message": message,
        }
        super().__init__(message)


class RunBudgetController:
    """
    Centralized budget enforcement for a single pipeline run.

    Usage:
        budget = RunBudgetController(BudgetLimits(...))
        budget.check("tokens")           # Raises if tokens exceeded
        budget.record_tokens(1500)       # Record usage
        budget.record_cost(0.02)         # Record cost
        budget.record_files(1, 15)       # Record file/line changes
        budget.increment_iteration()     # Record patch iteration
    """

    def __init__(self, limits: BudgetLimits):
        self.limits = limits
        self.usage = BudgetUsage()
        self._lock = threading.Lock()
        self._tripped = False
        self._trip_report: Optional[Dict[str, Any]] = None

    @property
    def is_tripped(self) -> bool:
        return self._tripped

    @property
    def trip_report(self) -> Optional[Dict[str, Any]]:
        return self._trip_report

    def check(self, category: str = "all") -> None:
        """
        Check if any budget limit has been breached.
        Raises BudgetExhaustedError if so.
        """
        with self._lock:
            if self._tripped:
                raise BudgetExhaustedError(
                    self._trip_report["category"],
                    self._trip_report["current_value"],
                    self._trip_report["limit_value"],
                    f"Circuit breaker already tripped: {self._trip_report['message']}"
                )

            checks = {
                "tokens": (self.usage.tokens_used, self.limits.max_tokens, "Token budget exhausted"),
                "cost": (self.usage.cost_usd, self.limits.max_cost_usd, "Cost budget exhausted"),
                "time": (self.usage.elapsed_seconds, self.limits.max_seconds, "Execution time limit exceeded"),
                "files": (self.usage.files_modified, self.limits.max_files_modified, "Maximum files modified exceeded"),
                "lines": (self.usage.lines_changed, self.limits.max_lines_changed, "Maximum lines changed exceeded"),
                "iterations": (self.usage.patch_iterations, self.limits.max_patch_iterations, "Maximum patch iterations exceeded"),
            }

            targets = [category] if category != "all" else list(checks.keys())

            for cat in targets:
                if cat in checks:
                    current, limit, msg = checks[cat]
                    if current > limit:
                        self._tripped = True
                        self._trip_report = {
                            "category": cat,
                            "current_value": str(current) if isinstance(current, float) else current,
                            "limit_value": str(limit) if isinstance(limit, float) else limit,
                            "message": msg,
                        }
                        raise BudgetExhaustedError(cat, current, limit, msg)

    def record_tokens(self, count: int) -> None:
        with self._lock:
            self.usage.tokens_used += count
        self.check("tokens")

    def record_cost(self, amount: float) -> None:
        with self._lock:
            self.usage.cost_usd += amount
        self.check("cost")

    def record_files(self, file_count: int, line_count: int) -> None:
        with self._lock:
            self.usage.files_modified += file_count
            self.usage.lines_changed += line_count
        self.check("files")
        self.check("lines")

    def increment_iteration(self) -> None:
        with self._lock:
            self.usage.patch_iterations += 1

    def check_time(self) -> None:
        """Explicitly check time budget (called before expensive operations)."""
        self.check("time")

    def has_iterations_remaining(self) -> bool:
        with self._lock:
            return self.usage.patch_iterations < self.limits.max_patch_iterations

    def get_usage_report(self) -> Dict[str, Any]:
        """Returns current usage vs limits for reporting."""
        with self._lock:
            return {
                "tokens": {"used": self.usage.tokens_used, "limit": self.limits.max_tokens},
                "cost_usd": {"used": str(round(self.usage.cost_usd, 4)), "limit": str(self.limits.max_cost_usd)},
                "elapsed_seconds": {"used": str(round(self.usage.elapsed_seconds, 1)), "limit": self.limits.max_seconds},
                "files_modified": {"used": self.usage.files_modified, "limit": self.limits.max_files_modified},
                "lines_changed": {"used": self.usage.lines_changed, "limit": self.limits.max_lines_changed},
                "patch_iterations": {"used": self.usage.patch_iterations, "limit": self.limits.max_patch_iterations},
                "circuit_breaker_tripped": self._tripped,
                "trip_report": self._trip_report,
            }
