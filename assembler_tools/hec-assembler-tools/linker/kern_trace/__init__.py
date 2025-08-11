# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
@brief Package for handling kernel operation tracing and analysis.

This package provides utilities for parsing trace files and extracting kernel operation information.
"""

from linker.kern_trace.context_config import ContextConfig
from linker.kern_trace.kern_remap import remap_dinstrs_vars, remap_m_c_instrs_vars
from linker.kern_trace.kern_var import KernVar
from linker.kern_trace.kernel_info import InstrAct, KernelInfo, MinstrMapEntry
from linker.kern_trace.kernel_op import KernelOp
from linker.kern_trace.trace_info import TraceInfo

__all__ = [
    "KernVar",
    "ContextConfig",
    "KernelOp",
    "TraceInfo",
    "remap_dinstrs_vars",
    "remap_m_c_instrs_vars",
    "KernelInfo",
    "InstrAct",
    "MinstrMapEntry",
]
