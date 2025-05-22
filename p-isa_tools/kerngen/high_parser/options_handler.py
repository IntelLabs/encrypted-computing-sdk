# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""A module to process optional key/value dictionary parameters"""

from abc import ABC, abstractmethod


class OptionsDict(ABC):
    """Abstract class to hold the options key/value pairs"""

    op_name: str = ""
    op_value = None

    @abstractmethod
    def validate(self, value):
        """Abstract method, which defines how to valudate a value"""


class OptionsIntDict(OptionsDict):
    """Holds a key/value pair for options of type Int"""

    def __init__(self, name: str, min_val: int, max_val: int):
        self.min_val = min_val
        self.max_val = max_val
        self._op_name = name

    def validate(self, value: int):
        """Validate numeric options with min/max range"""
        if self.min_val < value < self.max_val:
            return True
        return False

    @property
    def op_value(self):
        """Get op_value"""
        return self._op_value

    @op_value.setter
    def op_value(self, value: int):
        """Set op_value"""
        if self.validate(value):
            self._op_value = int(value)
        else:
            raise ValueError(
                "{self.op_name} must be in range ({self.min_val}, {self.max_val}): {self.op_name}={self.op_value}"
            )


class OptionsIntBounds:
    """Holds min/max/default values for options of type Int"""

    int_min: int
    int_max: int
    default: int | None

    def __init__(self, int_min: int, int_max: int, default: int | None):
        self.int_min = int_min
        self.int_max = int_max
        self.default = default


class OptionsDictFactory(ABC):
    """Abstract class that creates OptionsDict objects"""

    MAX_DIGIT = 3
    MIN_DIGIT = 0
    options = {
        "num_digits": OptionsIntBounds(MIN_DIGIT, MAX_DIGIT, None),
    }

    @staticmethod
    @abstractmethod
    def create(name: str, value) -> OptionsDict:
        """Abstract method, to define how to create an OptionsDict"""


class OptionsIntDictFactory(OptionsDictFactory):
    """OptionsDict parameter factory for Int types"""

    @staticmethod
    def create(name: str, value: int) -> OptionsIntDict:
        """Create a OptionsInt object based on key/value pair"""
        if name in OptionsIntDictFactory.options:
            if isinstance(OptionsIntDictFactory.options[name], OptionsIntBounds):
                options_int = OptionsIntDict(
                    name,
                    OptionsIntDictFactory.options[name].int_min,
                    OptionsIntDictFactory.options[name].int_max,
                )
                options_int.op_value = value
            # add other options types here
        else:
            raise KeyError(f"Invalid options name: '{name}'")
        return options_int


class OptionsDictFactoryDispatcher:
    """An object dispatcher based on key/value pair"""

    @staticmethod
    def create(name: str, value) -> OptionsDict:
        """Creat an OptionsDict object based on the type of value passed in"""
        if value.isnumeric():
            value = int(value)
        match value:
            case int():
                return OptionsIntDictFactory.create(name, value)
            case _:
                raise ValueError(f"Current type '{type(value)}' is not supported.")


class OptionsDictParser:
    """Parses key/value pairs and returns a dictionary of options"""

    @staticmethod
    def __default_values():
        default_dict = {}
        for key, val in OptionsDictFactory.options.items():
            default_dict[key] = val.default
        return default_dict

    @staticmethod
    def parse(options: list[str]):
        """Parse the options list and return a dictionary with values"""
        output_dict = OptionsDictParser.__default_values()
        for option in options:
            try:
                key, value = option.split("=")
                output_dict[key] = OptionsDictFactoryDispatcher.create(
                    key, value
                ).op_value
            except ValueError as err:
                raise ValueError(
                    f"Options must be key/value pairs (e.g. num_digits=3): '{option}'"
                ) from err
        return output_dict
