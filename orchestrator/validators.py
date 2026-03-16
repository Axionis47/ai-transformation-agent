"""Pipeline stage validators — enforce contracts between agents."""
from __future__ import annotations

from agents.base import AgentError
from orchestrator.schemas import MaturityResult, SignalSet, UseCase


def validate_signals(
    result: dict, agent_tag: str = "SIGNAL_EXTRACTOR"
) -> SignalSet | AgentError:
    """Validate signal extractor output. Returns SignalSet or AgentError."""
    try:
        signal_set = SignalSet(**result)
    except Exception as e:
        return AgentError(
            code="VALIDATION_FAIL",
            message=f"Signal validation: {e}",
            recoverable=True,
            agent_tag=agent_tag,
        )

    # Assign signal_ids if missing
    for i, sig in enumerate(signal_set.signals):
        if not sig.signal_id:
            sig.signal_id = f"sig-{i + 1:03d}"

    signal_set.signal_count = len(signal_set.signals)

    if signal_set.signal_count >= 6:
        signal_set.confidence_level = "HIGH"
    elif signal_set.signal_count >= 3:
        signal_set.confidence_level = "MEDIUM"
    else:
        signal_set.confidence_level = "LOW"

    return signal_set


def validate_maturity(
    result: dict, agent_tag: str = "MATURITY_SCORER"
) -> MaturityResult | AgentError:
    """Validate maturity scorer output. Returns MaturityResult or AgentError."""
    try:
        maturity = MaturityResult(**result)
    except Exception as e:
        return AgentError(
            code="VALIDATION_FAIL",
            message=f"Maturity validation: {e}",
            recoverable=True,
            agent_tag=agent_tag,
        )

    required_dims = {
        "data_infrastructure",
        "ml_ai_capability",
        "strategy_intent",
        "operational_readiness",
    }
    missing = required_dims - set(maturity.dimensions.keys())
    if missing:
        return AgentError(
            code="VALIDATION_FAIL",
            message=f"Missing dimensions: {missing}",
            recoverable=True,
            agent_tag=agent_tag,
        )

    return maturity


def validate_use_cases(
    result: list[dict], agent_tag: str = "USE_CASE_GENERATOR"
) -> list[UseCase] | AgentError:
    """Validate use case generator output. Returns list[UseCase] or AgentError."""
    try:
        use_cases = [UseCase(**uc) for uc in result]
    except Exception as e:
        return AgentError(
            code="VALIDATION_FAIL",
            message=f"UseCase validation: {e}",
            recoverable=True,
            agent_tag=agent_tag,
        )

    if len(use_cases) < 2:
        return AgentError(
            code="VALIDATION_FAIL",
            message=f"Need at least 2 use cases, got {len(use_cases)}",
            recoverable=True,
            agent_tag=agent_tag,
        )

    for uc in use_cases:
        if uc.tier == "HARD_EXPERIMENT" and uc.confidence > 0.65:
            uc.confidence = 0.65

    return use_cases
