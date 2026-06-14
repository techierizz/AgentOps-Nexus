"""
AgentOps Nexus — Execution State Machine

Replaces implicit procedural orchestration with a formal state machine.
Every transition is explicit, logged, and auditable.
"""
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
import traceback


class ExecutionState(str, Enum):
    """All possible states in the autonomous execution pipeline."""
    INIT = "init"
    LOAD_ISSUE = "load_issue"
    INDEX_REPO = "index_repo"
    SEARCH_MEMORY = "search_memory"
    HYPOTHESIZE = "hypothesize"
    VALIDATE_RCA = "validate_rca"
    GENERATE_PATCH = "generate_patch"
    VALIDATE_PATCH = "validate_patch"
    SECURITY_SCAN = "security_scan"
    RUN_TESTS = "run_tests"
    REFLECT = "reflect"
    EVALUATE_CONFIDENCE = "evaluate_confidence"
    MERGE_DECISION = "merge_decision"
    CREATE_PR = "create_pr"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLBACK = "rollback"
    BUDGET_EXHAUSTED = "budget_exhausted"
    RCA_CONFLICT = "rca_conflict"


@dataclass
class Transition:
    """A single state transition rule."""
    from_state: ExecutionState
    to_state: ExecutionState
    condition: Optional[str] = None  # Human-readable condition description


# ─── Transition Table ────────────────────────────────────────
# Defines ALL legal state transitions. No implicit jumps allowed.
TRANSITION_TABLE: List[Transition] = [
    # Happy path
    Transition(ExecutionState.INIT, ExecutionState.LOAD_ISSUE),
    Transition(ExecutionState.LOAD_ISSUE, ExecutionState.INDEX_REPO),
    Transition(ExecutionState.INDEX_REPO, ExecutionState.SEARCH_MEMORY),
    Transition(ExecutionState.SEARCH_MEMORY, ExecutionState.HYPOTHESIZE),
    Transition(ExecutionState.HYPOTHESIZE, ExecutionState.VALIDATE_RCA),

    # RCA success → patch loop
    Transition(ExecutionState.VALIDATE_RCA, ExecutionState.GENERATE_PATCH, "rca_validated"),
    # RCA conflict → skip patch loop
    Transition(ExecutionState.VALIDATE_RCA, ExecutionState.RCA_CONFLICT, "rca_conflict_detected"),

    # Patch loop
    Transition(ExecutionState.GENERATE_PATCH, ExecutionState.VALIDATE_PATCH),
    Transition(ExecutionState.VALIDATE_PATCH, ExecutionState.SECURITY_SCAN, "patch_safe"),
    Transition(ExecutionState.VALIDATE_PATCH, ExecutionState.ROLLBACK, "patch_unsafe"),
    Transition(ExecutionState.SECURITY_SCAN, ExecutionState.RUN_TESTS),
    Transition(ExecutionState.RUN_TESTS, ExecutionState.EVALUATE_CONFIDENCE, "tests_passed"),
    Transition(ExecutionState.RUN_TESTS, ExecutionState.REFLECT, "tests_failed"),

    # Reflection → retry patch (if iterations remain)
    Transition(ExecutionState.REFLECT, ExecutionState.ROLLBACK, "retry_available"),
    Transition(ExecutionState.REFLECT, ExecutionState.EVALUATE_CONFIDENCE, "max_iterations_reached"),

    # Rollback → re-enter patch generation
    Transition(ExecutionState.ROLLBACK, ExecutionState.GENERATE_PATCH, "rollback_complete"),

    # Post-patch evaluation
    Transition(ExecutionState.EVALUATE_CONFIDENCE, ExecutionState.MERGE_DECISION),
    Transition(ExecutionState.MERGE_DECISION, ExecutionState.CREATE_PR, "merge_allowed"),
    Transition(ExecutionState.MERGE_DECISION, ExecutionState.FAILED, "merge_rejected"),

    # RCA conflict path
    Transition(ExecutionState.RCA_CONFLICT, ExecutionState.EVALUATE_CONFIDENCE),

    # PR → done
    Transition(ExecutionState.CREATE_PR, ExecutionState.COMPLETED),

    # Budget exhaustion → from any state
    # (handled specially — see can_transition)

    # Terminal compensation transitions
    Transition(ExecutionState.BUDGET_EXHAUSTED, ExecutionState.FAILED),
]

# Build lookup index: from_state → list of valid (to_state, condition)
_TRANSITION_INDEX: Dict[ExecutionState, List[Transition]] = {}
for t in TRANSITION_TABLE:
    _TRANSITION_INDEX.setdefault(t.from_state, []).append(t)


def get_valid_transitions(from_state: ExecutionState) -> List[Transition]:
    """Returns all legal transitions from the given state."""
    return _TRANSITION_INDEX.get(from_state, [])


def can_transition(from_state: ExecutionState, to_state: ExecutionState) -> bool:
    """Check if a transition is legal."""
    # Budget exhaustion can be reached from any non-terminal state
    if to_state == ExecutionState.BUDGET_EXHAUSTED and from_state not in (
        ExecutionState.COMPLETED, ExecutionState.FAILED, ExecutionState.BUDGET_EXHAUSTED
    ):
        return True

    # Any state can transition to FAILED on unrecoverable error
    if to_state == ExecutionState.FAILED and from_state not in (
        ExecutionState.COMPLETED, ExecutionState.FAILED
    ):
        return True

    transitions = _TRANSITION_INDEX.get(from_state, [])
    return any(t.to_state == to_state for t in transitions)


@dataclass
class StateTransitionRecord:
    """Immutable record of a state transition for audit trail."""
    from_state: str
    to_state: str
    condition: Optional[str]
    timestamp: str
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class ExecutionStateMachine:
    """
    Drives the autonomous execution pipeline through explicit state transitions.

    Usage:
        sm = ExecutionStateMachine()
        sm.transition_to(ExecutionState.LOAD_ISSUE)
        sm.transition_to(ExecutionState.INDEX_REPO)
        ...
    """

    def __init__(self):
        self._current_state = ExecutionState.INIT
        self._history: List[StateTransitionRecord] = []
        self._is_terminal = False

    @property
    def current_state(self) -> ExecutionState:
        return self._current_state

    @property
    def history(self) -> List[StateTransitionRecord]:
        return list(self._history)

    @property
    def is_terminal(self) -> bool:
        return self._current_state in (
            ExecutionState.COMPLETED,
            ExecutionState.FAILED,
        )

    def transition_to(
        self,
        target: ExecutionState,
        condition: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Transition to a new state. Raises ValueError if transition is illegal.
        """
        if self.is_terminal:
            raise IllegalTransitionError(
                f"Cannot transition from terminal state {self._current_state.value}"
            )

        if not can_transition(self._current_state, target):
            valid = [t.to_state.value for t in get_valid_transitions(self._current_state)]
            raise IllegalTransitionError(
                f"Illegal transition: {self._current_state.value} → {target.value}. "
                f"Valid targets: {valid}"
            )

        import datetime
        record = StateTransitionRecord(
            from_state=self._current_state.value,
            to_state=target.value,
            condition=condition,
            timestamp=datetime.datetime.now().isoformat(),
            duration_ms=duration_ms,
            error=error,
        )
        self._history.append(record)
        self._current_state = target

    def force_fail(self, error: str) -> None:
        """Force transition to FAILED from any non-terminal state (emergency stop)."""
        if not self.is_terminal:
            import datetime
            record = StateTransitionRecord(
                from_state=self._current_state.value,
                to_state=ExecutionState.FAILED.value,
                condition="forced_failure",
                timestamp=datetime.datetime.now().isoformat(),
                error=error,
            )
            self._history.append(record)
            self._current_state = ExecutionState.FAILED

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Returns the full transition history as serializable dicts."""
        return [
            {
                "from": r.from_state,
                "to": r.to_state,
                "condition": r.condition,
                "timestamp": r.timestamp,
                "duration_ms": r.duration_ms,
                "error": r.error,
            }
            for r in self._history
        ]


class IllegalTransitionError(Exception):
    """Raised when an illegal state transition is attempted."""
    pass
