# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for kernel operation representation and analysis."""

from linker.kern_trace.context_config import ContextConfig
from linker.kern_trace.kern_var import KernVar


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
    valid_schemes = ["bgv", "ckks", "bfv"]

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

    def get_kern_var_objs(self, kern_var_strs: list[str]) -> list[KernVar]:
        """
        @brief Converts a list of kernel variable strings to KernVar objects.

        @param kern_var_strs: A list of strings representing kernel variables.

        @return list: A list of KernVar objects created from the input strings.
        """
        return [KernVar.from_string(var_str) for var_str in kern_var_strs]

    def get_level(self, kern_vars: list[KernVar]) -> int:
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
        self._vars = self.get_kern_var_objs(kern_args)
        self._level = self.get_level(self._vars)
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

    @property
    def expected_in_kern_file_name(self) -> str:
        """
        @brief Returns the expected file prefix for the kernel operation.

        @return str: The expected file prefix formatted as:
                     "{scheme}_{name}_{poly_modulus_degree}_l{level}_m{keyrns_terms}"
        """
        return self._expected_in_kern_file_name
