#!/usr/bin/env python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Compile Protocol Buffer files to Python modules.
This script can be run standalone without CMake/C++ dependencies.
"""

import sys
from pathlib import Path

from grpc_tools import protoc


def compile_protos():
    """Compile all .proto files to Python modules."""

    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()

    # The script is now in test/, so go up one level to data_formats
    if script_dir.name == "test":
        base_dir = script_dir.parent
    else:
        # Fallback: try to find data_formats from repo root
        base_dir = Path.cwd() / "p-isa_tools" / "data_formats"
        if not base_dir.exists():
            base_dir = script_dir.parent

    proto_dir = base_dir / "proto" / "heracles"
    python_dir = base_dir / "python"

    # Create output directory for generated files
    output_dir = python_dir / "heracles" / "proto"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py in proto directory
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text("# Auto-generated proto package\n")

    # Find all .proto files
    proto_files = list(proto_dir.glob("*.proto"))

    if not proto_files:
        print(f"No .proto files found in {proto_dir}")
        return 1

    print(f"Found {len(proto_files)} proto files to compile:")
    for proto_file in proto_files:
        print(f"  - {proto_file.name}")

    # Find the grpcio_tools package to get the google protobuf includes
    import grpc_tools

    grpc_tools_path = Path(grpc_tools.__file__).parent
    proto_include = grpc_tools_path / "_proto"

    # Compile all proto files at once to handle dependencies
    print("Compiling all proto files...")

    # protoc arguments - compile all files together
    args = [
        "grpc_tools.protoc",
        f"-I{proto_include}",  # Include path for google/protobuf/*.proto
        f"--proto_path={proto_dir}",
        f"--python_out={output_dir}",
    ] + [str(proto_file) for proto_file in proto_files]

    # Run protoc
    result = protoc.main(args)

    if result != 0:
        print("Error compiling proto files")
        return result

    print(f"\nSuccessfully compiled {len(proto_files)} proto files to {output_dir}")

    # Fix imports in generated files to use relative imports
    print("\nFixing imports in generated files...")
    for py_file in output_dir.glob("*_pb2.py"):
        content = py_file.read_text()

        # Replace absolute imports with relative imports for local proto files
        for proto_file in proto_files:
            module_name = proto_file.stem
            old_import = f"import {module_name}_pb2"
            new_import = f"from . import {module_name}_pb2"
            content = content.replace(old_import, new_import)

        py_file.write_text(content)
        print(f"  Fixed imports in {py_file.name}")

    print("\nProto compilation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(compile_protos())
