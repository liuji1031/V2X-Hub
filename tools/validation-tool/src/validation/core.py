"""Core functions for the validation package."""
from typing import Union

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


def validate(key, val, fcn_map: dict):
    """Validate the data using the validator map.

    Args:
        key: the key to be validated
        val: the value to be validated
        fcn_map: the validator function map, mapping from key to validator function
    """
    _key = _strip_brackets(key)
    print(f"validating, {key} -> {_key}")
    if _key not in fcn_map:
        return ""
    try:
        fcn = fcn_map[_key]
        fcn(val)  # run validation function
        return ""
    except Exception as e:
        return f"Validation failed for field {key} with value {val}: {e}"


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
    validator_map: dict, data: Union[dict, list], err_msgs: list, parent_key: str = ""
):  
    """Validate the data recursively using the validator map.

    Args:
        validator_map[str, Any]: the validator map, mapping from key to validator 
            function
        data: the data to be validated
        err_msgs: the list of error messages
        parent_key: the parent key
    """
    if _strip_brackets(parent_key) in validator_map:
        # if parent key already defined in map, check entire value instead of
        # individual fields separately, only do this for dict
        msg = validate(parent_key, data, validator_map)
        if msg:
            err_msgs.append(msg)
        return

    if isinstance(data, dict):
        for key, val in data.items():
            child_key = gen_child_key(parent_key, key)
            if isinstance(val, dict) or isinstance(val, list):
                validate_recursive(validator_map, val, err_msgs, child_key)
            else:
                msg = validate(child_key, val, validator_map)
                if msg:
                    err_msgs.append(msg)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child_key = gen_child_key(parent_key, "", idx)
            if isinstance(item, dict) or isinstance(item, list):
                validate_recursive(validator_map, item, err_msgs, child_key)
            else:
                msg = validate(child_key, item, validator_map)
                if msg:
                    err_msgs.append(msg)
    else:
        pass
