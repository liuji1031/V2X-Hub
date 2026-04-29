from j2735_202409 import ITIS, Common, TravelerInformation
from typing import Any
from copy import deepcopy


def ITIScodesAndText_validator(data: Any):
    """Custom validator for ITIScodesAndText class

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
    print("validating ITIS")
    assert isinstance(data, list), "value is not a list"

    # process the list into the expected list of dict[str, tuple]
    for d in data:
        _d = deepcopy(d)  # not to modify original value
        val = _d["item"]
        assert len(val) == 1
        assert isinstance(val, dict)
        for k, v in val.items():  # asserted only one value
            _d["item"] = (k, v)

    # finally call the PyCrate object
    ITIS.ITIScodesAndText.set_val(_d)
    print("validated ITIScodesAndText")
