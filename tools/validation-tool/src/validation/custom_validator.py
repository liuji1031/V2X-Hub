"""Custom validator classes.

This is useful to expanding the logic of the basic validator functions, e.g., adding
preprocessing steps before validation, custom sequence validation, etc. This is meant to
be expandable to add more complex validation logic if needed.
"""

from abc import ABC, abstractmethod
from typing import Any


class CustomValidator(ABC):
    """Base class for custom validators.

    Subclasses must implement the __call__ method, which takes the data to be validated
    """

    @abstractmethod
    def __call__(self, data: Any):
        """Validate the data

        Args:
            data: the data to be validated

        Raises:
            Exception: if validation fails
        """
        raise NotImplementedError(
            "CustomValidator subclasses must implement __call__"
        )


class SequenceOfValidator(CustomValidator):
    """Validate SEQUENCE of objects."""

    def __init__(self, validator_fcn, valid_range: tuple) -> None:
        """Initialization

        Args:
            validator_fcn: the validation function for each item in the SEQUENCE
            valid_range: a tuple of (min, max) number of items in the SEQUENCE
                        (inclusive)
        """
        assert callable(validator_fcn), "validator_fcn must be callable"
        assert isinstance(valid_range, tuple) and len(valid_range) == 2, (
            "valid_range must be a tuple of min and max"
        )
        assert isinstance(valid_range[0], int) and isinstance(
            valid_range[1], int
        ), "valid_range values must be integers"
        assert valid_range[0] >= 0 and valid_range[1] >= valid_range[0], (
            "valid_range must have non-negative integers with max >= min"
        )
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
            f"number of items in SEQUENCE out of valid range ({self.valid_range[0]}...{self.valid_range[1]})"
        )
        for i, d in enumerate(data):
            try:
                self.validator_fcn(d)
            except Exception as e:
                raise Exception(f"validation failed for item {i}: {e}")


class PreprocessValidator(CustomValidator):
    """Add preprocessing before validation."""

    def __init__(self, validator_fcn, preprocess_fcn):
        """Initialization

        Args:
            validator_fcn: the validation function for the field
            preprocess_fcn: the preprocessing function to be applied before validation
        """
        assert callable(validator_fcn), "validator_fcn must be callable"
        assert callable(preprocess_fcn), "preprocess_fcn must be callable"
        self.validator_fcn = validator_fcn
        self.preprocess_fcn = preprocess_fcn

    def __call__(self, data: Any):
        """Preprocess and validate the data

        Args:
            data: the data to be validated

        Raises:
            Exception: if validation fails
        """
        try:
            preprocessed_data = self.preprocess_fcn(data)
        except Exception as e:
            raise Exception(f"Preprocessing error: {e}")
        # validation error will be raised by the validator_fcn
        self.validator_fcn(preprocessed_data)


class ChoiceValidator(CustomValidator):
    """Validate CHOICE fields."""

    def __init__(self, choice_map: dict):
        """Initialization

        Args:
            choice_map: a dict mapping each possible CHOICE key to its validation
            function or any other callable that raises an exception if validation fails,
            e.g., other validators
        """
        assert isinstance(choice_map, dict), "choice_map must be a dict"
        for k, v in choice_map.items():
            assert callable(v), (
                f"validation function for choice '{k}' must be callable"
            )
        self.choice_map = choice_map

    def __call__(self, data: Any):
        """Validate the CHOICE field

        Args:
            data: the data to be validated, expected to be a dict with exactly one key

        Raises:
            Exception: if validation fails
        """
        assert isinstance(data, dict), "CHOICE value must be a dict"
        assert len(data) == 1, "CHOICE must have exactly one item"
        for k, v in data.items():
            assert k in self.choice_map, f"wrong CHOICE key: {k}"
            self.choice_map[k](v)
            return
