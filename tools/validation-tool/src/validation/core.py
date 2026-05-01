"""Core functions for the validation package."""

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Union
from src.validation.custom_validator import MultipleErrors

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
    error_msg: str = field(repr=False)  # type: ignore

    # hidden from init and repr, will be set by custom setter
    _error_msg: str = field(init=False, repr=False)

    @property
    def error_msg(self):
        return self._error_msg

    @error_msg.setter
    def error_msg(self, msg: str):
        """Custom setter for error_msg.

        The error message from pycrate uses the following format:
        <some failure message>, <value of the field that failed validation>
        The custom setter removes the part after comma
        """
        self._error_msg = msg.split(",")[0]

    def __repr__(self):
        return (
            f"ValidationError(key={self.key!r}, val={self.val!r}, "
            f"error_msg={self._error_msg!r})"
        )


def _validate_value(parent_key: str, val: Any, validator, errors: list):
    """Run a single validator callable on a value, appending errors if it fails."""
    logger.debug(f"validating: {parent_key}")
    try:
        logger.debug(f"\t {validator}({val})")
        validator(val)
    except Exception as e:
        if isinstance(e, MultipleErrors):
            # returned from SequenceOfValidator, meaning val is guaranteed to be a
            # list
            for idx, sub_e in e.errors:
                errors.append(
                    ValidationError(
                        f"{parent_key}[{idx}]", val[idx], str(sub_e)
                    )
                )
        else:
            errors.append(ValidationError(parent_key, val, str(e)))


def validate_required_keys(
    validator_map: dict, data: dict, errors: list, parent_key: str
):
    """Validate that the data contains all required keys.

    Args:
        validator_map: the nested validator map
        data: the data to be validated
        errors: the list of ValidationError objects
        parent_key: the current nesting path (string), used for error reporting
    """
    assert REQUIRED in validator_map
    for req_key in validator_map[REQUIRED]:
        if req_key not in data:
            errors.append(
                ValidationError(
                    parent_key,
                    None,
                    f"Missing required field: {req_key}",
                )
            )


def gen_child_key(parent_key: str, key: str, idx: Union[int, None] = None):
    """Generate the child key from the parent key and the key.

    Example:
        parent_key = ""
        key = "dataFrames"
        idx = 0
        gen_child_key(parent_key, key, idx) -> "dataFrames[0]"

        parent_key = "dataFrames[0]"
        key = "msgId"
        idx = None
        gen_child_key(parent_key, key, idx) -> "dataFrames[0].msgId"

    Args:
        parent_key: the parent key
        key: the key
        idx: the index
    """
    if not parent_key:  # parent key empty
        assert key, "parent key and child key cannot both be empty"
        out = key
    else:  # parent key non-empty
        if key:
            out = parent_key + "." + key
        else:
            out = parent_key
    if idx is not None:
        out += f"[{idx}]"
    return out


def _strip_brackets(s: str):
    out_s = ""
    i = 0
    while i < len(s):
        if s[i] == "[":
            while i < len(s) and s[i] != "]":
                i += 1
            i += 1  # one past the ']'
        if i < len(s):
            out_s += s[i]
            i += 1
        else:
            break
    return out_s


def validate_choice_val(val: Any):
    assert isinstance(val, dict), "value of a CHOICE field must be a dictionary"
    assert len(val) == 1, "CHOICE fields must have length of 1 dictionary"


def preprocess_choice_recursive(
    parent_handle: Union[dict, list],
    curr_key: Union[str, int],
    curr_data: Union[list, dict],
    choice_set: set,
) -> Union[dict, list]:
    """Recursively check if a field is CHOICE field and reorganize data.

    PyCrate expects this from the CHOICE field
    ```yaml
    a:  # CHOICE
        b: c
    ```

    Then the correct format for PyCrate is {"a":("b", "c")}
    Returns:
        processed data dictionary or list
    """
    if curr_key in choice_set:
        validate_choice_val(curr_data)
        k, v = next(iter(curr_data.items()))  # type: ignore
        if isinstance(v, dict):
            processed_v = {
                _k: preprocess_choice_recursive(v, _k, _v, choice_set)
                for _k, _v in v.items()
            }
            parent_handle[curr_key] = (k, processed_v)  # type: ignore
        elif isinstance(v, list):
            processed_v = [
                preprocess_choice_recursive(v, _k, _v, choice_set)
                for _k, _v in enumerate(v)
            ]
            parent_handle[curr_key] = (k, processed_v)  # type: ignore
        else:
            parent_handle[curr_key] = (k, v)  # type: ignore
    else:
        if isinstance(curr_data, dict):
            for key, val in curr_data.items():
                preprocess_choice_recursive(curr_data, key, val, choice_set)
        elif isinstance(curr_data, list):
            for idx, item in enumerate(curr_data):
                preprocess_choice_recursive(curr_data, idx, item, choice_set)

    return curr_data

def preprocess_choices(data: dict, choice_set: set) -> dict:
    """Transform all CHOICE fields in data to PyCrate tuple format in-place.
    Args:
        data: the message dictionary to preprocess
        choice_set: set of field names that are CHOICE types
    """
    for key, val in data.items():
        preprocess_choice_recursive(data, key, val, choice_set)
    return data


def validate_recursive(
    validator_map: dict,
    choice_set: set,
    data: Union[dict, list],
    errors: list,
    parent_key: str = "",
    skip_self: bool = False,
):
    """Validate the data by co-traversing a nested validator map alongside the data.

    The validator map mirrors the expected message structure. Reserved keys:
        - "__self__": a callable applied to the current node's value as a whole
        - "__required__": a list of child key names that must exist in the data

    Args:
        validator_map, dict[str, Any]: the nested validator map
        chice_set, set[str]: a set defining which attribute is a CHOICE field,
                            which needs to be handled differently
        data: the data to be validated
        errors: the list of ValidationError objects
        parent_key: the current nesting path (string), used for error reporting
        skip_self: whether to skip the SELF check, useful for list items where the SELF
            key may still be present for individual items
    """
    # validator map represents the schema corresponding to the current parent_key
    # data is essentially the value corresponding to parent_key
    if SELF in validator_map and not skip_self:
        _validate_value(parent_key, data, validator_map[SELF], errors)

    if isinstance(data, list):
        for idx, item in enumerate(data):
            child_key = gen_child_key(parent_key, "", idx)
            if isinstance(item, (dict, list)):
                # validator_map stays at the same level, apply the same schema to
                # each item in list
                # note: skip_self is set to True
                validate_recursive(
                    validator_map,
                    choice_set,
                    item,
                    errors,
                    child_key,
                    skip_self=True,
                )
        return

    if isinstance(data, dict):
        # check required keys at current level if defined
        if REQUIRED in validator_map:
            validate_required_keys(validator_map, data, errors, parent_key)

        # iterate through the keys in data, retrieve the corresponding validator from
        # the validator_map, and validate recursively
        for key, val in data.items():
            if key in RESERVED_KEYS:
                # it is assumed that the reserved keys will NOT appear in real data
                logger.warning(
                    f"data contains reserved key {key} at {parent_key}, skipping validation for this key"
                )
                continue
            if key not in validator_map:
                # skip if not required to validate, e.g., optional fields
                continue

            child_key = gen_child_key(parent_key, key)
            child_val_map = validator_map[key]
            if callable(child_val_map):
                # map directly to a validator function
                _validate_value(child_key, val, child_val_map, errors)
            elif isinstance(child_val_map, dict):
                # nested validator map, validate recursively
                # the type of val will be automatically handled in the recursive call
                # i.e., list, dict or other
                validate_recursive(
                    child_val_map, choice_set, val, errors, child_key
                )
