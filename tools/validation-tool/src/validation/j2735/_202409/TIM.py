from copy import deepcopy
from typing import Any

from j2735_202409 import ITIS, Common, TravelerInformation

from src.validation.custom_validator import (
    PreprocessValidator,
    SequenceOfValidator,
    ChoiceValidator,
)
from src.validation.core import SELF, REQUIRED


def ITIScodesAndText_preprocess(data: Any):
    """Preprocess function for ITIScodesAndText class

    An example ITIScodesAndText field in TraverlerInformation is as follows:
    ```yaml
    advisory:
      - item:
          itis: 257
      - item:
          text: "Stopped traffic"
    ```

    For PyCrate, need to convert the above into a list of tuple:
    [{"item": ("itis", 257)}, {"item": ("item", "Stopped traffic")}]
    """
    try:
        # process the list into the expected list of dict[str, tuple]
        # provided the input conform to standard
        assert isinstance(data, list)
        _data = deepcopy(data)  # not to modify original value
        for d in _data:
            val = d["item"]
            assert len(val) == 1
            assert isinstance(val, dict)
            for k, v in val.items():  # asserted only one value
                d["item"] = (k, v)
        return _data
    except Exception as e:
        return data  # return original data if preprocessing fails


MANDATORY_VALIDATOR_MAP = {
    "required": ["msgCnt", "dataFrames"],  # mandatory fields
    "msgCnt": Common.MsgCount.set_val,
    "dataFrames": {
        SELF: SequenceOfValidator(lambda x: None, (1, 8)),
        REQUIRED: [
            "frameType",
            "msgId",
            "startTime",
            "durationTime",
            "priority",
            "regions",
            "content",
        ],  # mandatory fields
        "frameType": TravelerInformation.TravelerInfoType.set_val,
        "msgId": ChoiceValidator(
            {
                "roadSignID": TravelerInformation.RoadSignID.set_val,
                "furtherInfoID": Common.FurtherInfoID.set_val,
            }
        ),
        "startTime": Common.MinuteOfTheYear.set_val,
        "durationTime": TravelerInformation.MinutesDuration.set_val,
        "priority": TravelerInformation.SignPriority.set_val,
        "regions": SequenceOfValidator(
            TravelerInformation.GeographicalPath.set_val, (1, 16)
        ),
        "content": ChoiceValidator(
            {
                "advisory": PreprocessValidator(
                    ITIS.ITIScodesAndText.set_val, ITIScodesAndText_preprocess
                ),
                "workZone": PreprocessValidator(
                    TravelerInformation.WorkZone.set_val,
                    ITIScodesAndText_preprocess,
                ),
                "genericSign": PreprocessValidator(
                    TravelerInformation.GenericSignage.set_val,
                    ITIScodesAndText_preprocess,
                ),
                "speedLimit": PreprocessValidator(
                    TravelerInformation.SpeedLimit.set_val,
                    ITIScodesAndText_preprocess,
                ),
                "exitService": PreprocessValidator(
                    TravelerInformation.ExitService.set_val,
                    ITIScodesAndText_preprocess,
                ),
            }
        ),
    },
}
