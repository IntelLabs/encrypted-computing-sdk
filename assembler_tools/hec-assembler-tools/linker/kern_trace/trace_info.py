# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for parsing and analyzing trace files."""

import os

from assembler.instructions import tokenize_from_line

from linker.kern_trace.context_config import ContextConfig
from linker.kern_trace.kernel_op import KernelOp


class TraceInfo:
    """
    @brief Class for handling trace files.

    @details This class provides an interface
    and functionality for handling trace file info.
    """

    def __init__(self, filename: str):
        """
        @brief Initializes a TraceFile instance.

        @param filename: The name of the trace file.
        """
        self._trace_file = filename

    def __str__(self):
        return f"TraceFile(trace_file={self._trace_file})"

    def get_trace_file(self) -> str:
        """
        @brief Returns the trace file name.

        @return str: The name of the trace file.
        """
        return self._trace_file

    def get_param_index_dict(self, tokens: list[str]) -> dict:
        """
        @brief Returns a dictionary mapping property names to their indices in the trace file.

        @return dict: A dictionary mapping property names to their indices.
        """
        param_idxs = {}
        for i, token in enumerate(tokens):
            param_idxs[token] = i
        return param_idxs

    def extract_context_and_args(self, tokens, param_idxs, line_num):
        """
        @brief Extract context configuration and arguments from tokens.

        @param tokens: List of tokens from a trace file line.
        @param param_idxs: Dictionary mapping parameter names to their indices.
        @param line_num: Current line number for error reporting.

        @return tuple: A tuple containing (context_config, kern_args).
        """
        try:
            # Extract required parameters
            name = tokens[param_idxs["instruction"]]
            scheme = tokens[param_idxs["scheme"]]
            poly_mod_degree = int(tokens[param_idxs["poly_modulus_degree"]])
            keyrns_terms = int(tokens[param_idxs["keyrns_terms"]])

            # Create scheme configuration
            context_config = ContextConfig(scheme, poly_mod_degree, keyrns_terms)

            # Collect all parameters from the trace file line that start with "arg"
            kern_args = []
            arg_keys = [key for key in param_idxs if key.startswith("arg")]
            arg_keys.sort()
            for arg_key in arg_keys:
                if param_idxs[arg_key] < len(tokens) and tokens[param_idxs[arg_key]]:
                    kern_args.append(tokens[param_idxs[arg_key]])

            return name, context_config, kern_args

        except KeyError as e:
            raise KeyError(f"Missing required parameter in line {line_num} with tokens: {tokens}: {e}") from e
        except IndexError as e:
            raise ValueError(f"Invalid number of parameters in line {line_num}: {e}") from e
        except ValueError as e:
            raise ValueError(f"Invalid value in line {line_num}: {e}") from e

    def parse_kernel_ops(self) -> list[KernelOp]:
        """
        @brief Parses the kernel operations from the trace file.

        @return list: A list of KernelOp instances parsed from the trace file.
        """
        # Validate that trace file exists
        if not os.path.isfile(self._trace_file):
            raise FileNotFoundError(f"Trace file not found: {self._trace_file}")

        kernel_ops: list = []

        with open(self._trace_file, encoding="utf-8") as file:
            lines = file.readlines()

            if not lines:
                return kernel_ops

            # Process header line to get parameter indices
            header_tokens, _ = tokenize_from_line(lines[0])
            param_idxs = self.get_param_index_dict(header_tokens)

            # Process the rest of the lines to get kernel operations
            for line_num, line in enumerate(lines[1:], 2):  # Start at line 2 (index+1)
                tokens, _ = tokenize_from_line(line.strip())

                if not tokens or not tokens[0]:  # Skip empty lines
                    continue

                name, context_config, kern_args = self.extract_context_and_args(tokens, param_idxs, line_num)

                # Create and add KernelOp with all arguments
                kernel_op = KernelOp(name, context_config, kern_args)
                kernel_ops.append(kernel_op)

        return kernel_ops

    @classmethod
    def parse_kernel_ops_from_file(cls, filename: str) -> list[KernelOp]:
        """
        @brief Parses kernel operations from a given trace file.

        @param filename: The name of the trace file.
        @return list: A list of KernelOp instances parsed from the trace file.
        """
        trace_info = cls(filename)
        return trace_info.parse_kernel_ops()
