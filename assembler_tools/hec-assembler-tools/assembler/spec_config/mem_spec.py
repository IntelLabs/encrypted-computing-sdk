import os
import json
from assembler.common.constants import Constants, MemoryModel

class MemSpecConfig:

    _target_attributes = {
        "bytes_per_xinstruction": Constants.setXInstructionSizeBytes,
        "max_instructions_per_bundle": Constants.setMaxBundleSize,
        "xinst_queue_size_in_bytes": MemoryModel.setMaxXInstQueueCapacity,
        "cinst_queue_size_in_bytes": MemoryModel.setMaxCInstQueueCapacity,
        "minst_queue_size_in_bytes": MemoryModel.setMaxMInstQueueCapacity,
        "store_buffer_size_in_bytes": MemoryModel.setMaxStoreBufferCapacity,
        "num_blocks_per_twid_meta_word": MemoryModel.setNumBlocksPerTwidMetaWord,
        "num_blocks_per_kgseed_meta_word": MemoryModel.setNumBlocksPerKgseedMetaWord,
        "num_routing_table_registers": MemoryModel.setNumRoutingTableRegisters,
        "num_ones_meta_registers": MemoryModel.setNumOnesMetaRegisters,
        "num_twiddle_meta_registers": MemoryModel.setNumTwiddleMetaRegisters,
        "twiddle_meta_register_size_in_bytes": MemoryModel.setTwiddleMetaRegisterSizeBytes,
        "max_residuals": MemoryModel.setMaxResiduals,
        "num_register_banks": MemoryModel.setNumRegisterBanks,
        "num_registers_per_bank": MemoryModel.setNumRegistersPerBank,
        "hbm_size_in_bytes": MemoryModel.HBM.setMaxCapacity,
        "cache_size_in_bytes": MemoryModel.SPAD.setMaxCapacity,
    }

    @classmethod
    def dump_mem_spec_to_json(cls, filename):
        """
        Dumps the attributes of all classes as a JSON file under the "mem_spec" section.

        Args:
            filename (str): The name of the JSON file to write to.
        """

        # Initialize an empty dictionary to hold all hardware specifications
        hw_specs = {}

        # Aggregate hardware specifications from each class into a single dictionary
        hw_specs.update(Constants.hw_spec_as_dict())
        hw_specs.update(MemoryModel.hw_spec_as_dict())
        hw_specs.update(MemoryModel.HBM.hw_spec_as_dict())
        hw_specs.update(MemoryModel.SPAD.hw_spec_as_dict())

        # Wrap the hw_specs in a top-level dictionary
        output_dict = {"mem_spec": hw_specs}

        # Write the dictionary to a JSON file
        with open(filename, 'w') as json_file:
            json.dump(output_dict, json_file, indent=4)

    @classmethod
    def init_mem_spec_from_json(cls, filename):
        """
        Updates class attributes using methods specified in the target_attributes dictionary based on a JSON file.
        This method checks wether values found on json file exists in target dictionaries. 

        Args:
            filename (str): The name of the JSON file to read from.
        """
        with open(filename, 'r') as json_file:
            data = json.load(json_file)

        # Check for the "mem_spec" section
        if "mem_spec" not in data:
            raise ValueError("The JSON file does not contain the 'mem_spec' section.")

        mem_spec = data["mem_spec"]

        for key, value in mem_spec.items():
            if key not in cls._target_attributes:
                raise ValueError(f"Attribute key '{key}' is not valid.")
            else:
                update_method = cls._target_attributes[key]
                update_method(value)
    
    @classmethod
    def initialize_mem_spec(cls, module_dir, mem_spec_file):

        if not mem_spec_file:
            mem_spec_file = os.path.join(module_dir, "config/mem_spec.json")
            mem_spec_file = os.path.abspath(mem_spec_file)

        if not os.path.exists(mem_spec_file):
            raise FileNotFoundError(
                f"Required Mem Spec file not found: {mem_spec_file}\n"
                "Please provide a valid path using the `mem_spec` option, "
                "or use a valid default file at: `<assembler dir>/config/mem_spec.json`."
                )
        
        cls.init_mem_spec_from_json(mem_spec_file)

        return mem_spec_file
