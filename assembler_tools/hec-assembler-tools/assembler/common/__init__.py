# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os


def makeUniquePath(path: str) -> str:
    """
    Returns a unique, normalized, and absolute version of the given file path.

    Args:
        path (str): The file path to be processed.

    Returns:
        str: A unique, normalized, and absolute version of the input path.
    """
    return os.path.normcase(os.path.realpath(os.path.expanduser(path)))
