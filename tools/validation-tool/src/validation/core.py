"""Core functions for the validation package."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Union

log_level = os.getenv("VALIDATION_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level
    if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    else "INFO",
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SELF = "__self__"
REQUIRED = "__required__"
RESERVED_KEYS = {SELF, REQUIRED}


@dataclass
class ValidationError:
    key: str
    val: Any
    error_msg: str


def _format_path(path: list) -> str:
    """Join a path list into a human-readable dot-separated string.

    Args:
        path: list of keys, where index entries are formatted as "[i]"
    """
    result = ""
    for part in path:
        if part.startswith("["):
            result += part
        else:
            if result:
                result += "."
            result += part
    return result or "(root)"


def _validate_value(path: list, val: Any, validator, errors: list):
    """Run a single validator callable on a value, appending errors if it fails."""
    path_str = _format_path(path)
    logger.debug(f"validating: {path_str}")
    try:
        logger.debug(f"\t {validator}({val})")
        validator(val)
    except Exception as e:
        errors.append(ValidationError(path_str, val, f"Validation failed: {e}"))


def _validate_choice(path: list, val: Any, choice_map: dict, errors: list):
    """Validate a CHOICE field: data must be a dict with exactly one key that
    exists in the choice_map.
    """
    path_str = _format_path(path)
    logger.debug(f"validating CHOICE: {path_str}")
    try:
        assert isinstance(val, dict), "CHOICE value must be a dict"
        assert len(val) == 1, "CHOICE must have exactly one item"
        for k, v in val.items():
            assert k in choice_map, f"wrong CHOICE key: {k}"
            logger.debug(f"\t CHOICE {k}: {choice_map[k]}({v})")
            choice_map[k](v)
    except Exception as e:
        errors.append(ValidationError(path_str, val, f"Validation failed: {e}"))


def validate_required_keys(
    validator_map: dict, data: dict, errors: list, path: list
):
    """Validate that the data contains all required keys.

    Args:
        validator_map: the nested validator map
        data: the data to be validated
        errors: the list of ValidationError objects
        path: the current nesting path (list of keys), used for error reporting
    """
    assert "required" in validator_map
    for req_key in validator_map["required"]:
        if req_key not in data:
            errors.append(
                ValidationError(
                    _format_path(path + [req_key]),
                    None,
                    f"Missing required field: {req_key}",
                )
            )


def validate_recursive(
    validator_map: dict,
    data: Union[dict, list],
    errors: list,
    path: list | None = None,
):
    """Validate the data by co-traversing a nested validator map alongside the data.

    The validator map mirrors the expected message structure. Reserved keys:
        - "__self__": a callable applied to the current node's value as a whole
        - "__required__": a list of child key names that must exist in the data

    Args:
        validator_map: the nested validator map
        data: the data to be validated
        errors: the list of ValidationError objects
        path: the current nesting path (list of keys), used for error reporting
    """
    if path is None:
        path = []

    if SELF in validator_map:
        _validate_value(path, data, validator_map[SELF], errors)

    if isinstance(data, list):
        for idx, item in enumerate(data):
            child_path = path + [f"[{idx}]"]
            if isinstance(item, (dict, list)):
                validate_recursive(validator_map, item, errors, child_path)
        return

    if isinstance(data, dict):
        if REQUIRED in validator_map:
            validate_required_keys(validator_map, data, errors, path)

        for key, val in data.items():
            if key in RESERVED_KEYS or key not in validator_map:
                continue
            child_path = path + [key]
            node = validator_map[key]

            if callable(node):
                _validate_value(child_path, val, node, errors)
            elif isinstance(node, dict):
                if isinstance(val, (dict, list)):
                    validate_recursive(node, val, errors, child_path)
                else:
                    if SELF in node:
                        _validate_value(child_path, val, node[SELF], errors)
