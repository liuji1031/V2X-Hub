from typing import Union
from functools import partial

from j2735_202409 import ITIS, Common, TravelerInformation

TIM_VALIDATOR_MAP = {
    "msgCnt": Common.MsgCount,
    "dataFrames.msgId.roadSignID": TravelerInformation.RoadSignID.set_val,
    "dataFrames.msgId.furtherInfoID": Common.FurtherInfoID.set_val,
    "dataFrames.startTime": Common.MinuteOfTheYear.set_val,
    "dataFrames.durationTime": TravelerInformation.MinutesDuration.set_val,
    "dataFrames.priority": TravelerInformation.SignPriority.set_val,
    "dataFrames.regions": TravelerInformation.GeographicalPath.set_val,
    # "dataFFrames.content.advisory": ITIS.ITIScodesAndText,
    # "dataFrames.content.workZone": TravelerInformation.WorkZone,
}


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
    _key = _strip_brackets(key)
    if _key not in fcn_map:
        return ""
    try:
        fcn = fcn_map[_key]
        fcn(val)  # run validation function
        return ""
    except Exception as e:
        return f"Validation failed for field {key} with value {val}: {e}"


_validate = partial(validate, fcn_map=TIM_VALIDATOR_MAP)


def gen_child_key(parent_key: str, key: str, idx: Union[int, None] = None):
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
    data: Union[dict, list], err_msgs: list, parent_key: str = ""
):
    if _strip_brackets(parent_key) in TIM_VALIDATOR_MAP:
        # if parent key already defined in map, check entire value instead of
        # individual fields separately
        msg = _validate(parent_key, data)
        if msg:
            err_msgs.append(msg)
        return

    if isinstance(data, dict):
        for key, val in data.items():
            child_key = gen_child_key(parent_key, key)
            if isinstance(val, dict) or isinstance(val, list):
                validate_recursive(val, err_msgs, child_key)
            else:
                msg = _validate(child_key, val)
                if msg:
                    err_msgs.append(msg)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            child_key = gen_child_key(parent_key, "", idx)
            if isinstance(item, dict) or isinstance(item, list):
                validate_recursive(item, err_msgs, child_key)
            else:
                msg = _validate(child_key, item)
                if msg:
                    err_msgs.append(msg)
    else:
        pass
