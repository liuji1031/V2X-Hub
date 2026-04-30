import os
from src.validation.j2735._202409 import (
    MESSAGE_VALIDATORS as j2735_202409_MESSAGE_VALIDATORS,
)
from src.validation.core import validate_recursive

STANDARDS = {"j2735_202409": j2735_202409_MESSAGE_VALIDATORS}

DEFAULT_STANDARD = os.getenv("VALIDATION_STANDARD", "j2735_202409")


def validate_message(
    data: dict, message_type: str, standard: str = DEFAULT_STANDARD
) -> list:
    """Validate a message against a standard's validator map.

    Args:
        data: the decoded message dict
        message_type: e.g. "TIM", "BSM"
        standard: the standard revision key, defaults to the latest
    """
    if standard not in STANDARDS:
        raise ValueError(f"unknown standard: {standard}")
    registry = STANDARDS[standard]
    if message_type not in registry:
        raise ValueError(f"no validator for {message_type} in {standard}")
    validator_map = registry[message_type]
    err_msgs = []
    validate_recursive(validator_map, data, err_msgs)
    return err_msgs


def validate_TIM(data: dict) -> list:
    """Validate a TIM message against the default standard."""
    return validate_message(data, "TIM")
