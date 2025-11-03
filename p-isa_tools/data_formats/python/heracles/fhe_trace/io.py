# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


# TODO: create also C++ variants of below; given how simple and stable these functions should be just in replicated form, not shared code

from heracles.proto.fhe_trace_pb2 import Trace

# load & store functions
# ===============================


def store_trace(filename: str, trace: Trace):
    """
    Serialize and store a HEC trace. Filename is constructed by concatenating `filename_prefix` with standard suffix.
    Prefix can contain directory paths, although they must all be existing directories
    """
    with open(filename, "wb") as f:
        f.write(trace.SerializeToString())


def load_trace(filename: str) -> Trace:
    """
    Load and deserialize a HEC trace. Filename is constructed by concatenating `filename_prefix` with standard suffix.
    Prefix can contain directory paths, although they must all be existing directories
    """
    trace = Trace()
    with open(filename, "rb") as f:
        trace.ParseFromString(f.read())
    return trace
