# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one
# or more Intel-operated generative artificial intelligence solutions

"""@brief Base class for kernel operations in trace files."""

import os
from dataclasses import dataclass
from assembler.instructions import tokenize_from_line


class KernVar:
    """
    @brief Class representing a kernel variable in trace files.

    @details This class encapsulates the properties of a kernel variable,
    including its label, degree, and level.
    """

    def __init__(self, label: str, degree: int, level: int):
        """
        @brief Initializes a KernVar instance.

        @param label: The label of the kernel variable.
        @param degree: The polynomial degree of the variable.
        @param level: The current RNS level of the variable.
        """
        self._label = label
        self._degree = degree
        self._level = level

    @classmethod
    def from_string(cls, var_str: str):
        """
        @brief Creates a KernVar instance from a string representation.

        @param var_str: The string representation of the kernel variable in the format "label_degree_level".

        @return KernVar: An instance of KernVar initialized with the parsed values.
        """
        parts = var_str.split("_")
        if len(parts) != 3:
            raise ValueError(f"Invalid kernel variable string format: {var_str}")

        label = parts[0]
        degree = int(parts[1])
        level = int(parts[2])

        return cls(label, degree, level)

    @property
    def label(self) -> str:
        """
        @brief Returns the label of the kernel variable.

        @return str: The label of the kernel variable.
        """
        return self._label

    @property
    def degree(self) -> int:
        """
        @brief Returns the polynomial degree of the kernel variable.

        @return int: The polynomial degree of the kernel variable.
        """
        return self._degree

    @property
    def level(self) -> int:
        """
        @brief Returns the current RNS level of the kernel variable.

        @return int: The current RNS level of the kernel variable.
        """
        return self._level


@dataclass
class ContextConfig:
    """
    @brief Configuration class for encryption scheme parameters.

    @details This class encapsulates the parameters related to an encryption scheme,
    including the scheme name, polynomial modulus degree, and key RNS terms.
    """

    scheme: str
    poly_mod_degree: int
    keyrns_terms: int


class KernelOp:
    """
    @brief Base class for kernel operations in trace files.

    @details This class serves as a base for all kernel operations, providing a common interface
    and functionality for handling kernel operations in trace files.
    """

    # List of valid kernel operation names.
    valid_kernel_ops = [
        "add",
        "sub",
        "mul",
        "relin",
        "mod_switch",
        "add_plain",
        "rotate",
        "ntt",
        "intt",
        "square",
        "mul_plain",
        "rescale",
    ]

    # List of valid encryption schemes.
    valid_schemes = ["bgv", "ckks"]

    def _get_expected_in_kern_file_name(
        self,
        name: str,
        context_config: ContextConfig,
        level: int,
    ) -> str:
        """
        @brief Returns the expected kernel file name based on internal params.

        @param name: The name of the kernel operation.
        @param context_config: Configuration object containing encryption scheme parameters.
        @param level: The current RNS level.

        @return str: The expected kernel file name formatted as:
                     "{scheme}_{name}_{poly_modulus_degree}_l{level}_m{keyrns_terms}"
        """
        return (
            f"{context_config.scheme.lower()}_"
            f"{name.lower()}_"
            f"{context_config.poly_mod_degree}_"
            f"l{level}_"
            f"m{context_config.keyrns_terms}"
        )

    def _get_kern_var_objs(self, kern_var_strs: list[str]) -> list[KernVar]:
        """
        @brief Converts a list of kernel variable strings to KernVar objects.

        @param kern_var_strs: A list of strings representing kernel variables.

        @return list: A list of KernVar objects created from the input strings.
        """
        return [KernVar.from_string(var_str) for var_str in kern_var_strs]

    def _get_level(self, kern_vars: list[KernVar]) -> int:
        """
        @brief Sets the level of the kernel operation based on input's current RNS level.

        @details The level is determined by current RNS level on input variables,
        which is used to categorize the kernel operation.
        """
        if not kern_vars:
            raise ValueError(
                "Kernel operation must have at least one variable to determine level."
            )

        # Assuming all input variables have the same level for the operation
        return kern_vars[1].level if len(kern_vars) > 1 else kern_vars[0].level

    def __init__(
        self,
        name: str,
        context_config: ContextConfig,
        kern_args: list,
    ):
        """
        @brief Initializes a KernelOp instance.

        @param name: The name of the kernel operation.
        @param context_config: Configuration object containing encryption scheme parameters.
        @param kern_args: List of arguments for the kernel operation.
        """

        if name.lower() not in self.valid_kernel_ops:
            raise ValueError(
                f"Invalid kernel operation name: {name}. "
                f"Valid names are: {', '.join(self.valid_kernel_ops)}"
            )
        if context_config.scheme.lower() not in self.valid_schemes:
            raise ValueError(
                f"Invalid encryption scheme: {context_config.scheme}. "
                f"Valid schemes are: {', '.join(self.valid_schemes)}"
            )
        if len(kern_args) < 2:
            raise ValueError("Kernel operation must have at least two arguments.")

        self._name = name
        self._scheme = context_config.scheme
        self._poly_modulus_degree = context_config.poly_mod_degree
        self._keyrns_terms = context_config.keyrns_terms
        self._vars = self._get_kern_var_objs(kern_args)
        self._level = self._get_level(self._vars)
        self._expected_in_kern_file_name = self._get_expected_in_kern_file_name(
            name,
            context_config,
            self._level,
        )

    def __str__(self):
        """
        @brief Returns a string representation of the KernelOp instance.
        """
        return f"KernelOp(name={self.name})"

    @property
    def kern_vars(self) -> list:
        """
        @brief Returns the arguments of the kernel operation.

        @return list: A list of arguments for the kernel operation.
        """
        return self._vars

    @property
    def name(self) -> str:
        """
        @brief Returns the name of the kernel operation.

        @return str: The name of the kernel operation.
        """
        return self._name

    @property
    def scheme(self) -> str:
        """
        @brief Returns the encryption scheme used by the kernel operation.

        @return str: The encryption scheme (e.g., BGV, CKKS).
        """
        return self._scheme

    @property
    def poly_modulus_degree(self) -> int:
        """
        @brief Returns the polynomial modulus degree of the kernel operation.

        @return int: The polynomial modulus degree.
        """
        return self._poly_modulus_degree

    @property
    def keyrns_terms(self) -> int:
        """
        @brief Returns the number of key RNS terms for the kernel operation.

        @return int: The number of key RNS terms.
        """
        return self._keyrns_terms

    @property
    def level(self) -> int:
        """
        @brief Returns the current RNS level of the kernel operation.

        @return int: The current RNS level.
        """
        return self._level


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

    def _get_param_index_dict(self, tokens: list[str]) -> dict:
        """
        @brief Returns a dictionary mapping property names to their indices in the trace file.

        @return dict: A dictionary mapping property names to their indices.
        """
        param_idx = {}
        for i, token in enumerate(tokens):
            param_idx[token] = i
        return param_idx

    def _extract_context_and_args(self, tokens, param_idx, line_num):
        """
        @brief Extract context configuration and arguments from tokens.

        @param tokens: List of tokens from a trace file line.
        @param param_idx: Dictionary mapping parameter names to their indices.
        @param line_num: Current line number for error reporting.

        @return tuple: A tuple containing (context_config, kern_args).
        """
        try:
            # Extract required parameters
            name = tokens[param_idx["name"]]
            scheme = tokens[param_idx["scheme"]]
            poly_mod_degree = int(tokens[param_idx["poly_modulus_degree"]])
            keyrns_terms = int(tokens[param_idx["keyrns_terms"]])

            # Create scheme configuration
            context_config = ContextConfig(scheme, poly_mod_degree, keyrns_terms)

            # Collect all parameters from the trace file line that start with "arg"
            kern_args = []
            arg_keys = [key for key in param_idx if key.startswith("arg")]
            arg_keys.sort()
            for arg_key in arg_keys:
                if param_idx[arg_key] < len(tokens) and tokens[param_idx[arg_key]]:
                    kern_args.append(tokens[param_idx[arg_key]])

            return name, context_config, kern_args

        except KeyError as e:
            raise KeyError(f"Missing required parameter in line {line_num}: {e}") from e
        except IndexError as e:
            raise ValueError(
                f"Invalid number of parameters in line {line_num}: {e}"
            ) from e
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

        with open(self._trace_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

            if not lines:
                return kernel_ops

            # Process header line to get parameter indices
            header_tokens, _ = tokenize_from_line(lines[0])
            param_idx = self._get_param_index_dict(header_tokens)

            # Process the rest of the lines to get kernel operations
            for line_num, line in enumerate(lines[1:], 2):  # Start at line 2 (index+1)
                tokens, _ = tokenize_from_line(line)

                if not tokens or not tokens[0]:  # Skip empty lines
                    continue

                name, context_config, kern_args = self._extract_context_and_args(
                    tokens, param_idx, line_num
                )

                # Create and add KernelOp with all arguments
                kernel_op = KernelOp(name, context_config, kern_args)
                kernel_ops.append(kernel_op)

        return kernel_ops
