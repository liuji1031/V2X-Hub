from typing import Any


class SequenceOfValidator:
    """Validate SEQUENCE of objects."""

    def __init__(self, validator_fcn, valid_range: tuple) -> None:
        """Initialization

        Args:
            validator_fcn: the validation function for each item in the SEQUENCE
            valid_range: a tuple of (min, max) number of items in the SEQUENCE (inclusive)
        """
        self.validator_fcn = validator_fcn
        self.valid_range = valid_range

    def __call__(self, data: Any):
        """Validate the data

        Args:
            data: the data to be validated, expected to be a list of dict

        Raises:
            Exception: if validation fails
        """
        assert isinstance(data, list), "value is not a list"
        assert self.valid_range[0] <= len(data) <= self.valid_range[1], (
            f"number of items in SEQUENCE out of valid range {self.valid_range}"
        )
        for i, d in enumerate(data):
            try:
                self.validator_fcn(d)
            except Exception as e:
                raise Exception(f"validation failed for item {i}: {e}")


class PreprocessValidator:
    """Add preprocessing before validation."""

    def __init__(self, validator_fcn, preprocess_fcn):
        """Initialization

        Args:
            validator_fcn: the validation function for the field
            preprocess_fcn: the preprocessing function to be applied before validation
        """
        self.validator_fcn = validator_fcn
        self.preprocess_fcn = preprocess_fcn

    def __call__(self, data: Any):
        """Preprocess and validate the data

        Args:
            data: the data to be validated

        Raises:
            Exception: if validation fails
        """
        preprocessed_data = self.preprocess_fcn(data)
        self.validator_fcn(preprocessed_data)
