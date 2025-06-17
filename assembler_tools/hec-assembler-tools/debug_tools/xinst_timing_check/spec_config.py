# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""Configuration for the Xinst Timing Check ISA specification."""

import os
from assembler.spec_config.isa_spec import ISASpecConfig

import xinst  # pylint: disable=import-error


class XTCSpecConfig(ISASpecConfig):
    """
    Configuration class for the Xinst Timing Check ISA specification.
    This class defines the target operations, attributes, and methods for
    initializing the ISA specification from a JSON file.

    Methods:
        dump_isa_spec_to_json: Unimplemented for this child class.
        initialize_isa_spec: Initializes the ISA specification from a JSON file.
        dump_isa_spec_to_json: Unimplemented for this child class.
    Attributes:
        __target_xops: Dictionary mapping operation names to their corresponding
                       instruction classes in the xinst module.
        _target_ops: Dictionary containing the target operations for this ISA spec.
        _target_attributes: Dictionary mapping attribute names to their setter methods.
    """

    __target_xops = {
        "add": xinst.add.Instruction,
        "exit": xinst.exit_mod.Instruction,
        "intt": xinst.intt.Instruction,
        "mac": xinst.mac.Instruction,
        "maci": xinst.maci.Instruction,
        "move": xinst.move.Instruction,
        "mul": xinst.mul.Instruction,
        "muli": xinst.muli.Instruction,
        "nop": xinst.nop.Instruction,
        "ntt": xinst.ntt.Instruction,
        "rshuffle": xinst.rshuffle.Instruction,
        "sub": xinst.sub.Instruction,
        "twintt": xinst.twintt.Instruction,
        "twntt": xinst.twntt.Instruction,
        "xstore": xinst.xstore.Instruction,
    }

    _target_ops = {"xinst": __target_xops}

    _target_attributes = {
        "num_tokens": "SetNumTokens",
        "num_dests": "set_num_dests",
        "num_sources": "set_num_sources",
        "default_throughput": "set_default_throughput",
        "default_latency": "set_default_latency",
        "special_latency_max": "SetSpecialLatencyMax",
        "special_latency_increment": "SetSpecialLatencyIncrement",
    }

    @classmethod
    def dump_isa_spec_to_json(cls, filename):
        """
        Uninmplemented for this child class.
        """
        print("WARNING: 'dump_isa_spec_to_json' unimplemented for xinst_timing_check")

    @classmethod
    def initialize_isa_spec(cls, module_dir, isa_spec_file):

        if not isa_spec_file:
            isa_spec_file = os.path.join(module_dir, "../../config/isa_spec.json")
            isa_spec_file = os.path.abspath(isa_spec_file)

        if not os.path.exists(isa_spec_file):
            raise FileNotFoundError(
                f"Required ISA Spec file not found: {isa_spec_file}\n"
                "Please provide a valid path using the `isa_spec` option, "
                "or use a valid default file at: `<assembler dir>/config/isa_spec.json`."
            )

        cls.init_isa_spec_from_json(isa_spec_file)

        return isa_spec_file
