# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""
@file linker_run_config.py
@brief This module provides configuration for the linker process.
"""

import io
import os
from typing import Any

from assembler.common import makeUniquePath
from assembler.common.run_config import RunConfig


class LinkerRunConfig(RunConfig):
    """
    @class LinkerRunConfig
    @brief Maintains the configuration data for the run.

    @fn as_dict
    @brief Returns the configuration as a dictionary.

    @return dict The configuration as a dictionary.
    """

    # Type annotations for class attributes
    input_prefixes: list[str]
    input_mem_file: str
    using_trace_file: bool
    trace_file: str
    input_dir: str
    output_dir: str
    output_prefix: str

    __initialized = False  # specifies whether static members have been initialized
    # contains the dictionary of all configuration items supported and their
    # default value (or None if no default)
    __default_config: dict[str, Any] = {}

    def __init__(self, **kwargs):
        """
        @brief Constructs a new LinkerRunConfig Object from input parameters.

        See base class constructor for more parameters.

        @param input_prefixes List of input prefixes, including full path. For an input prefix, linker will
            assume there are three files named `input_prefixes[i] + '.minst'`,
            `input_prefixes[i] + '.cinst'`, and `input_prefixes[i] + '.xinst'`.
            This list must not be empty.
        @param output_prefix Prefix for the output file names.
            Three files will be generated:
            `output_dir/output_prefix.minst`, `output_dir/output_prefix.cinst`, and
            `output_dir/output_prefix.xinst`.
            Output filenames cannot match input file names.
        @param input_mem_file Input memory file associated with the result kernel.
        @param output_dir OPTIONAL directory where to store all intermediate files and final output.
            This will be created if it doesn't exists.
            Defaults to current working directory.

        @exception TypeError A mandatory configuration value was missing.
        @exception ValueError At least, one of the arguments passed is invalid.
        """
        super().__init__(**kwargs)

        self.init_default_config()

        # Validate input parameters
        if "hbm_size" in kwargs and kwargs["hbm_size"] is not None:
            if not isinstance(kwargs["hbm_size"], int):
                raise ValueError("Invalid param: hbm_size must be an integer")
            if kwargs["hbm_size"] < 0:
                raise ValueError("Invalid param: hbm_size must be a non-negative integer")

        if "has_hbm" in kwargs and not isinstance(kwargs["has_hbm"], bool):
            raise ValueError("Invalid param: has_hbm must be a boolean value")

        # class members based on configuration
        for config_name, default_value in self.__default_config.items():
            value = kwargs.get(config_name, default_value)
            print(f"Config: {config_name} = {value} default: {default_value}")
            if value is not None:
                setattr(self, config_name, value)
            else:
                if not hasattr(self, config_name):
                    setattr(self, config_name, default_value)
                    if getattr(self, config_name) is None:
                        raise TypeError(f"Expected value for configuration `{config_name}`, but `None` received.")

        # Fix file paths
        # E0203: Access to member 'input_mem_file' before its definition.
        # But it was defined in previous loop.
        if self.input_mem_file != "":  # pylint: disable=E0203
            self.input_mem_file = makeUniquePath(self.input_mem_file)
        if self.trace_file != "":
            self.trace_file = makeUniquePath(self.trace_file)

        self.output_dir = makeUniquePath(self.output_dir)
        self.input_dir = makeUniquePath(self.input_dir)

    @classmethod
    def init_default_config(cls):
        """
        @brief Initializes static members of the class.
        """
        if not cls.__initialized:
            cls.__default_config["input_prefixes"] = ""
            cls.__default_config["input_mem_file"] = ""
            cls.__default_config["using_trace_file"] = False
            cls.__default_config["trace_file"] = ""
            cls.__default_config["output_dir"] = os.getcwd()
            cls.__default_config["input_dir"] = os.getcwd()
            cls.__default_config["output_prefix"] = None
            cls.__default_config["keep_spad_boundary"] = False
            cls.__default_config["keep_hbm_boundary"] = False

            cls.__initialized = True

    def __str__(self):
        """
        @brief Provides a string representation of the configuration.

        @return str The string for the configuration.
        """
        self_dict = self.as_dict()
        with io.StringIO() as retval_f:
            for key, value in self_dict.items():
                print(f"{key}: {value}", file=retval_f)
            retval = retval_f.getvalue()
        return retval

    def as_dict(self) -> dict:
        """
        @brief Provides the configuration as a dictionary.

        @return dict The configuration.
        """
        retval = super().as_dict()
        tmp_self_dict = vars(self)
        retval.update({config_name: tmp_self_dict[config_name] for config_name in self.__default_config})
        return retval
