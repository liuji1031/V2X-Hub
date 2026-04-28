from typing import Union
from j2735_202409 import Common, TravelerInformation, ITIS

FIELD2TYPE_MAP = {
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

def _strip_brackets(s:str):
    out_s = ""
    i = 0
    while i<len(s):
        if s[i] == '[':
            while i<len(s) and s[i] != ']':
                i+=1
            i += 1  # one past the ']'
        if i<len(s):
            out_s += s[i]
            i += 1
        else:
            break
    return out_s

def _validate(key, val):
    _key = _strip_brackets(key)
    if _key not in FIELD2TYPE_MAP:
        return ""
    try:
        fcn = FIELD2TYPE_MAP[_key]
        fcn(val)
        return ""
    except Exception as e:
        return f"Validation failed for field {key} with value {val}: {e}"

def gen_child_key(parent_key: str, key:str, idx:Union[int, None]=None):
    out = parent_key + "." + key if parent_key else key
    if idx is not None:
        out += f"[{idx}]"
    return out


def validate_recursive(data : Union[dict, list],err_msgs:list, parent_key : str = ""):
    if isinstance(data, dict):
        for key, val in data.items():
            if isinstance(val, dict):
                validate_recursive(val, err_msgs, gen_child_key(parent_key, key))
            elif isinstance(val, list):
                validate_recursive(val, err_msgs, gen_child_key(parent_key, key))
            else:
                msg = _validate(key, val)
                if msg:
                    err_msgs.append(msg)
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                validate_recursive(item, err_msgs, gen_child_key(parent_key, key, idx))
            else:
                msg = _validate(parent_key + "." + key, item)
                if msg:
                    err_msgs.append(msg)
    else:
        pass