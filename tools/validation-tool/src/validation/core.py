"""Core functions for the validation package."""

import logging
import os
from typing import Union, Any

from dataclasses import dataclass
log_level = os.getenv("VALIDATION_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level
    if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    else "INFO",
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

CONT_TRAVERSAL = True  # to signal to continue traversing the sub-fields even if parent key has a hit in the validator map


def _strip_num_in_brackets(s: str):
    out_s = ""
    i = 0
    while i < len(s):
        out_s += s[i]
        if s[i] == "[":
            while i < len(s) and s[i] != "]":
                i += 1
            out_s += s[i]  # s[i] = ']'
        i += 1
    return out_s

@dataclass
class ValidationError:
    key: str
    val: Any
    error_msg: str

def validate(key, val, fcn_map: dict):
    """Validate the data using the validator map.

    Args:
        key: the key to be validated
        val: the value to be validated
        fcn_map: the validator function map, mapping from key to validator function
    """
    _key = _strip_num_in_brackets(key)
    logger.debug(f"validating: {key} -> {_key}")
    if _key not in fcn_map:
        return None
    try:
        fcn = fcn_map[_key]
        if isinstance(fcn, tuple):
            # when tuple is encountered, the first element is the validator function,
            # the second element is a flag to signal continuing traversal, irrelevant here
            fcn = fcn[0]
        if isinstance(fcn, dict):  # use dictionary to express CHOICE
            # in this case, val should also be a dict
            assert len(val) == 1, "CHOICE must have exactly one item"
            for k, v in val.items():
                logger.debug(f"\t, {fcn[k]}({v})")
                assert k in fcn, f"Wrong CHOICE key: {k}"
                fcn[k](v)
        else:
            logger.debug(f"\t {fcn}({val})")
            fcn(val)  # run validation function
        return None
    except Exception as e:
        return ValidationError(key, val, f"Validation failed: {e}")


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


def validate_recursive(
    validator_map: dict,
    data: Union[dict, list],
    errors: list[ValidationError],
    parent_key: str = "",
):
    """Validate the data recursively using the validator map.

    Args:
        validator_map[str, Any]: the validator map, mapping from key to validator
            function
        data: the data to be validated
        errors: the list of ValidationError objects
        parent_key: the parent key
    """
    _parent_key = _strip_num_in_brackets(parent_key)
    if _parent_key in validator_map:
        # if parent key already defined in map, validate the value in entirety first
        err = validate(parent_key, data, validator_map)
        if err:
            errors.append(err)
        entry = validator_map[_parent_key]
        if not (isinstance(entry, tuple) and len(entry) == 2 and entry[1] is CONT_TRAVERSAL):
            # check if a tuple is supplied and the second element is CONT_TRAVERSAL
            # if not, return. If yes, continue validating the sub-fields
            return

    if isinstance(data, dict):
        for key, val in data.items():
            child_key = gen_child_key(parent_key, key)
            if isinstance(val, dict) or isinstance(val, list):
                validate_recursive(validator_map, val, errors, child_key)
            else:
                err = validate(child_key, val, validator_map)
                if err:
                    errors.append(err)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child_key = gen_child_key(parent_key, "", idx)
            if isinstance(item, dict) or isinstance(item, list):
                validate_recursive(validator_map, item, errors, child_key)
            else:
                err = validate(child_key, item, validator_map)
                if err:
                    errors.append(err)
    else:
        pass
