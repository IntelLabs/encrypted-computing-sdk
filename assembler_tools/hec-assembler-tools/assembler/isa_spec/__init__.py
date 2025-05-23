import os
import json
import assembler.instructions.cinst as cinst
import assembler.instructions.minst as minst
import assembler.instructions.xinst as xinst

class SpecConfig:
    __target_cops = {
        "bload"     : cinst.bload.Instruction,
        "bones"     : cinst.bones.Instruction,
        "exit"      : cinst.cexit.Instruction,
        "cload"     : cinst.cload.Instruction,
        "nop"       : cinst.cnop.Instruction,
        "cstore"    : cinst.cstore.Instruction,
        "csyncm"    : cinst.csyncm.Instruction,
        "ifetch"    : cinst.ifetch.Instruction,
        "kgload"    : cinst.kgload.Instruction,
        "kgseed"    : cinst.kgseed.Instruction,
        "kgstart"   : cinst.kgstart.Instruction,
        "nload"     : cinst.nload.Instruction,
        "xinstfetch": cinst.xinstfetch.Instruction,
    }

    __target_xops = {
        "add"      : xinst.add.Instruction,
        "copy"     : xinst.copy_mod.Instruction,
        "exit"     : xinst.exit_mod.Instruction,
        "intt"     : xinst.intt.Instruction,
        "irshuffle": xinst.irshuffle.Instruction,
        "mac"      : xinst.mac.Instruction,
        "maci"     : xinst.maci.Instruction,
        "move"     : xinst.move.Instruction,
        "mul"      : xinst.mul.Instruction,
        "muli"     : xinst.muli.Instruction,
        "nop"      : xinst.nop.Instruction,
        "ntt"      : xinst.ntt.Instruction,
        "rshuffle" : xinst.rshuffle.Instruction,
        "sub"      : xinst.sub.Instruction,
        "twintt"   : xinst.twintt.Instruction,
        "twntt"    : xinst.twntt.Instruction,
        "xstore"   : xinst.xstore.Instruction,
    }

    __target_mops = {
        "mload" : minst.mload.Instruction,
        "mstore": minst.mstore.Instruction,
        "msyncc": minst.msyncc.Instruction,
    }

    _target_ops = {
        "xinst": __target_xops,
        "cinst": __target_cops,
        "minst": __target_mops  
    }

    _target_attributes = {
        "num_tokens"               : "SetNumTokens",
        "num_dests"                : "SetNumDests",
        "num_sources"              : "SetNumSources",
        "default_throughput"       : "SetDefaultThroughput",
        "default_latency"          : "SetDefaultLatency",
        "special_latency_max"      : "SetSpecialLatencyMax",
        "special_latency_increment": "SetSpecialLatencyIncrement",
    }

    @classmethod
    def dump_isa_spec_to_json(cls, filename):
        """
        Dumps the attributes of all ops' classes as a JSON file under the "isa_spec" section.

        Args:
            filename (str): The name of the JSON file to write to.
        """
        isa_spec_dict = {}

        for inst_type, ops in cls._target_ops.items():
            isa_spec_dict[inst_type] = {}

            for op_name, op in ops.items():
                # Call the as_dict method to get attributes
                class_dict = op.isa_spec_as_dict()
                # Store the attributes in the dictionary
                isa_spec_dict[inst_type][op_name] = class_dict

        # Wrap the isa_spec_dict in a top-level dictionary
        output_dict = {"isa_spec": isa_spec_dict}

        # Write the dictionary to a JSON file
        with open(filename, 'w') as json_file:
            json.dump(output_dict, json_file, indent=4)

    @classmethod
    def init_isa_spec_from_json(cls, filename):
        """
        Updates ops' class attributes using methods specified in the target_attributes dictionary based on a JSON file.
        This method checks wether values found on json file exists in target dictionaries. 

        Args:
            filename (str): The name of the JSON file to read from.
        """
        with open(filename, 'r') as json_file:
            data = json.load(json_file)

        # Check for the "isa_spec" section
        if "isa_spec" not in data:
            raise ValueError("The JSON file does not contain the 'isa_spec' section.")

        isa_spec = data["isa_spec"]

        for inst_type, ops in cls._target_ops.items():
            if inst_type not in isa_spec:
                raise ValueError(f"Instruction type '{inst_type}' is not found in the JSON file.")

            for op_name, op in ops.items():
                if op_name not in isa_spec[inst_type]:
                    raise ValueError(f"Operation '{op_name}' is not found in the JSON file for instruction type '{inst_type}'.")

                attributes = isa_spec[inst_type][op_name]

                for attr_name, value in attributes.items():
                    if attr_name in cls._target_attributes:
                        method_name = cls._target_attributes[attr_name]
                        setter = getattr(op, method_name)
                        setter(value)
                    else:
                        raise ValueError(f"Attribute '{attr_name}' is not recognized.")
    
    @classmethod
    def initialize_isa_spec(cls, module_dir, isa_spec_file):

        if not isa_spec_file:
            isa_spec_file = os.path.join(module_dir, "config/isa_spec.json")
            isa_spec_file = os.path.abspath(isa_spec_file)

        if not os.path.exists(isa_spec_file):
            raise FileNotFoundError(
                f"Required ISA Spec file not found: {isa_spec_file}\n"
                "Please provide a valid path using the `isa_spec` option, "
                "or use a valid default file at: `<assembler dir>/config/isa_spec.json`."
                )
        
        cls.init_isa_spec_from_json(isa_spec_file)

        return isa_spec_file
