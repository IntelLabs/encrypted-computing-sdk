# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Module providing an interface to pisa generators"""

import json
from importlib import import_module
from pathlib import Path


class GeneratorError(Exception):
    """Class representing errors raised by the Generators class"""


class Generators:
    """Class responsible for obtaining pisa ops from the pisa generators"""

    def __init__(self, dirpath: str, class_map: dict[str, list[str]]):
        """Initializer. Expects a path to a manifest JSON file and dictionary
        `{op : [classname, filename]}`"""
        self.map = class_map
        self.directory = dirpath

    @classmethod
    def from_manifest(cls, filepath: str, scheme: str):
        """Creates a `Generators` object given a manifest JSON file selected
        from the `scheme`. Parses the manifest file as a python dictionary and
        stores it in `self.map`"""
        filepath_p = Path(filepath)
        dirpath = str(filepath_p.parent)
        with open(filepath, encoding="utf-8") as manifest_file:
            manifest = json.load(manifest_file)
            try:
                return cls(dirpath, manifest[scheme.upper()])
            except KeyError as e:
                raise GeneratorError(
                    f"Scheme `{scheme.upper()}` not found in manifest file"
                ) from e

    def available_kernels(self) -> str:
        """Returns a list of available pisa ops."""
        return "\n".join(f"{op}" for op in self.map.keys())

    def get_kernel(self, opname: str):
        """Returns the kernel generator given a valid op name"""
        try:
            # Capitalize the opname because it is the name of the class!
            class_name, module_file = self.map[opname.upper()]
            filepath = Path(self.directory).stem + "/" + Path(module_file).stem
            module_path = filepath.replace("/", ".")

            # Actual import happens here
            module = import_module(module_path)
            return getattr(module, class_name)
        except KeyError as e:
            raise GeneratorError(f"Op not found in available pisa ops: {opname}") from e
        except AttributeError as e:
            raise GeneratorError(
                f"Class for op `{opname}` name not found: {class_name}"
            ) from e
        except ImportError as e:
            raise GeneratorError(f"Unable to import module: {module_path}") from e
