# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# These contents may have been developed with support from one or more Intel-operated
# generative artificial intelligence solutions

"""@brief Module for encryption scheme context configuration."""

from dataclasses import dataclass


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
