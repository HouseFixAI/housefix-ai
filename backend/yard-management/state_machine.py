"""
State machine logic for Yard Management System.
Validates state transitions and enforces business rules.
"""

from config import VALID_TRANSITIONS, DCS


class StateMachineError(Exception):
    pass


class InvalidTransitionError(StateMachineError):
    pass


class BusinessRuleError(StateMachineError):
    pass


def validate_transition(current_status: str, new_status: str) -> bool:
    """Check if transition from current_status to new_status is valid."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    return new_status in allowed


def transition(current_status: str, new_status: str, driver: dict | None = None,
               dc_config: dict | None = None) -> str:
    """
    Validate and execute a state transition. Returns the new status.
    Raises StateMachineError on invalid transitions.
    """
    if not validate_transition(current_status, new_status):
        raise InvalidTransitionError(
            f"Invalid transition: {current_status} → {new_status}. "
            f"Allowed: {VALID_TRANSITIONS.get(current_status, [])}"
        )

    # Business rules
    if new_status == "Actief_Dok" and driver and not driver.get("dock_id"):
        # When going to dock, a dock must be assigned
        raise BusinessRuleError("Cannot move to Actief_Dok without a dock assignment")

    if new_status == "Standby_Aangekomen" and current_status != "Standby_Onderweg":
        raise InvalidTransitionError("Standby_Aangekomen only allowed from Standby_Onderweg")

    return new_status


def get_allowed_transitions(status: str) -> list[str]:
    """Return list of allowed next states from current status."""
    return VALID_TRANSITIONS.get(status, [])


def is_terminal(status: str) -> bool:
    """Check if status is a terminal state (no further transitions)."""
    return status in ("Voltooid", "Geblokkeerd")


def should_early_call(driver: dict, dc_config: dict) -> bool:
    """
    Check if we should call the next driver early.
    Rule: Call next when current driver is halfway through dock time.
    """
    if not driver or driver["status"] != "Actief_Dok":
        return False

    from datetime import datetime, timedelta
    timeout = dc_config.get("timeout_dock_minuten", 10)
    halfway_minutes = timeout / 2

    if driver.get("status_updated_at"):
        updated = datetime.fromisoformat(driver["status_updated_at"])
        now = datetime.utcnow()
        elapsed = (now - updated).total_seconds() / 60
        return elapsed >= halfway_minutes

    return False


def get_call_next_strategy(dc_id: str, dc_config: dict, standby_count: int,
                           dock_count: int, active_dock_count: int) -> str:
    """
    Determine the call-next strategy:
    - "standby": call to standby spot
    - "direct_dock": call directly to dock (standby full)
    - "none": no call needed
    """
    if standby_count < dc_config.get("standby_slots", 2):
        return "standby"

    if active_dock_count < dock_count:
        return "direct_dock"

    return "none"
