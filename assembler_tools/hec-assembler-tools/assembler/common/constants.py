# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from .decorators import classproperty


class Constants:
    """
    Contains project level and global constants that won't fit logically into any other category.

    Attributes:
        KILOBYTE (int): Number of bytes in a kilobyte (2^10).
        MEGABYTE (int): Number of bytes in a megabyte (2^20).
        GIGABYTE (int): Number of bytes in a gigabyte (2^30).
        WORD_SIZE (int): Word size in bytes (32KB/word).

        REPLACEMENT_POLICY_FTBU (str): Identifier for the "furthest used" replacement policy.
        REPLACEMENT_POLICY_LRU (str): Identifier for the "least recently used" replacement policy.
        REPLACEMENT_POLICIES (tuple): Tuple containing all replacement policy identifiers.

        XINSTRUCTION_SIZE_BYTES (int): Size of an x-instruction in bytes.
        MAX_BUNDLE_SIZE (int): Maximum number of instructions in a bundle.
        MAX_BUNDLE_SIZE_BYTES (int): Maximum bundle size in bytes.

        TW_GRAMMAR_SEPARATOR (str): Separator for twiddle arguments used in grammar parsing.
        OPERATIONS (list): List of high-level operations supported by the system.
    """

    __MAX_BUNDLE_SIZE: int
    __XINSTRUCTION_SIZE_BYTES: int

    # Data Constants
    # --------------

    @classproperty
    def KILOBYTE(cls) -> int:
        """Number of bytes in a kilobyte (2^10)."""
        return 2**10

    @classproperty
    def MEGABYTE(csl) -> int:
        """Number of bytes in a megabyte (2^20)."""
        return 2**20

    @classproperty
    def GIGABYTE(cls) -> int:
        """Number of bytes in a gigabyte (2^30)."""
        return 2**30

    @classproperty
    def WORD_SIZE(cls) -> int:
        """Word size in bytes (32KB/word)."""
        return 32 * cls.KILOBYTE

    # Replacement Policies Constants
    # ------------------------------

    @classproperty
    def REPLACEMENT_POLICY_FTBU(cls) -> str:
        """Identifier for the "furthest used" replacement policy."""
        return "ftbu"

    @classproperty
    def REPLACEMENT_POLICY_LRU(cls) -> str:
        """Identifier for the "least recently used" replacement policy."""
        return "lru"

    @classproperty
    def REPLACEMENT_POLICIES(cls) -> tuple:
        """Tuple containing all replacement policy identifiers."""
        return (cls.REPLACEMENT_POLICY_FTBU, cls.REPLACEMENT_POLICY_LRU)

    # Misc Constants
    # --------------

    @classproperty
    def XINSTRUCTION_SIZE_BYTES(cls) -> int:
        """Size of an x-instruction in bytes."""
        return cls.__XINSTRUCTION_SIZE_BYTES

    @classproperty
    def MAX_BUNDLE_SIZE(cls) -> int:
        """Maximum number of instructions in a bundle."""
        return cls.__MAX_BUNDLE_SIZE

    @classproperty
    def MAX_BUNDLE_SIZE_BYTES(cls) -> int:
        """Maximum bundle size in bytes."""
        return cls.XINSTRUCTION_SIZE_BYTES * cls.MAX_BUNDLE_SIZE

    @classproperty
    def TW_GRAMMAR_SEPARATOR(cls) -> str:
        """
        Separator for twiddle arguments.

        Used in the grammar to parse the twiddle argument of an xntt kernel operation.
        """
        return "_"

    @classproperty
    def OPERATIONS(cls) -> list:
        """List of high-level operations supported by the system."""
        return [
            "add",
            "mul",
            "ntt",
            "intt",
            "relin",
            "mod_switch",
            "rotate",
            "square",
            "add_plain",
            "add_corrected",
            "mul_plain",
            "rescale",
            "boot_dot_prod",
            "boot_mod_drop_scale",
            "boot_mul_const",
            "boot_galois_plain",
        ]

    @classmethod
    def hw_spec_as_dict(cls) -> dict:
        """
        Returns hw configurable attributes as dictionary.
        """
        return {"bytes_per_xinstruction": cls.XINSTRUCTION_SIZE_BYTES, "max_instructions_per_bundle": cls.MAX_BUNDLE_SIZE}

    @classmethod
    def setMaxBundleSize(cls, val: int):
        """Updates max bundle size"""
        cls.__MAX_BUNDLE_SIZE = val

    @classmethod
    def setXInstructionSizeBytes(cls, val: int):
        """Updates size of single XInstruction"""
        cls.__XINSTRUCTION_SIZE_BYTES = val


def convertBytes2Words(bytes_in: int) -> int:
    """
    Converts a size in bytes to the equivalent number of words.

    Args:
        bytes (int): The size in bytes to be converted.

    Returns:
        int: The equivalent size in words.
    """
    return int(bytes_in / Constants.WORD_SIZE)


def convertWords2Bytes(words: int) -> int:
    """
    Converts a size in words to the equivalent number of bytes.

    Args:
        words (int): The size in words to be converted.

    Returns:
        int: The equivalent size in bytes.
    """
    return words * Constants.WORD_SIZE


class MemInfo:
    """
    Constants related to memory information, read from the P-ISA kernel memory file.

    This class provides a structured way to access various constants and keywords
    used in the P-ISA kernel memory file, including keywords for loading and storing
    data, metadata fields, and metadata targets.
    """

    class Keyword:
        """
        Keywords for loading memory information from the P-ISA kernel memory file.

        These keywords are used to identify different operations and data types
        within the memory file.
        """

        @classproperty
        def KEYGEN(cls):
            """Keyword for key generation."""
            return "keygen"

        @classproperty
        def LOAD(cls):
            """Keyword for data load operation."""
            return "dload"

        @classproperty
        def LOAD_INPUT(cls):
            """Keyword for loading input polynomial."""
            return "poly"

        @classproperty
        def LOAD_KEYGEN_SEED(cls):
            """Keyword for loading key generation seed."""
            return "keygen_seed"

        @classproperty
        def LOAD_ONES(cls):
            """Keyword for loading ones."""
            return "ones"

        @classproperty
        def LOAD_NTT_AUX_TABLE(cls):
            """Keyword for loading NTT auxiliary table."""
            return "ntt_auxiliary_table"

        @classproperty
        def LOAD_NTT_ROUTING_TABLE(cls):
            """Keyword for loading NTT routing table."""
            return "ntt_routing_table"

        @classproperty
        def LOAD_iNTT_AUX_TABLE(cls):
            """Keyword for loading iNTT auxiliary table."""
            return "intt_auxiliary_table"

        @classproperty
        def LOAD_iNTT_ROUTING_TABLE(cls):
            """Keyword for loading iNTT routing table."""
            return "intt_routing_table"

        @classproperty
        def LOAD_TWIDDLE(cls):
            """Keyword for loading twiddle factors."""
            return "twid"

        @classproperty
        def STORE(cls):
            """Keyword for data store operation."""
            return "dstore"

    class MetaFields:
        """
        Names of different metadata fields.
        """

        @classproperty
        def FIELD_KEYGEN_SEED(cls):
            return MemInfo.Keyword.LOAD_KEYGEN_SEED

        @classproperty
        def FIELD_ONES(cls):
            return MemInfo.Keyword.LOAD_ONES

        @classproperty
        def FIELD_NTT_AUX_TABLE(cls):
            return MemInfo.Keyword.LOAD_NTT_AUX_TABLE

        @classproperty
        def FIELD_NTT_ROUTING_TABLE(cls):
            return MemInfo.Keyword.LOAD_NTT_ROUTING_TABLE

        @classproperty
        def FIELD_iNTT_AUX_TABLE(cls):
            return MemInfo.Keyword.LOAD_iNTT_AUX_TABLE

        @classproperty
        def FIELD_iNTT_ROUTING_TABLE(cls):
            return MemInfo.Keyword.LOAD_iNTT_ROUTING_TABLE

        @classproperty
        def FIELD_TWIDDLE(cls):
            return MemInfo.Keyword.LOAD_TWIDDLE

    @classproperty
    def FIELD_KEYGENS(cls):
        return "keygens"

    @classproperty
    def FIELD_INPUTS(cls):
        return "inputs"

    @classproperty
    def FIELD_OUTPUTS(cls):
        return "outputs"

    @classproperty
    def FIELD_METADATA(cls):
        return "metadata"

    @classproperty
    def FIELD_METADATA_SUBFIELDS(cls):
        """Tuple of subfield names for metadata."""
        return (
            cls.MetaFields.FIELD_KEYGEN_SEED,
            cls.MetaFields.FIELD_TWIDDLE,
            cls.MetaFields.FIELD_ONES,
            cls.MetaFields.FIELD_NTT_AUX_TABLE,
            cls.MetaFields.FIELD_NTT_ROUTING_TABLE,
            cls.MetaFields.FIELD_iNTT_AUX_TABLE,
            cls.MetaFields.FIELD_iNTT_ROUTING_TABLE,
        )

    class MetaTargets:
        """
        Targets for different metadata.
        """

        @classproperty
        def TARGET_ONES(cls):
            """Special target register for Ones."""
            return 0

        @classproperty
        def TARGET_NTT_AUX_TABLE(cls):
            """Special target register for rshuffle NTT auxiliary table."""
            return 0

        @classproperty
        def TARGET_NTT_ROUTING_TABLE(cls):
            """Special target register for rshuffle NTT routing table."""
            return 1

        @classproperty
        def TARGET_iNTT_AUX_TABLE(cls):
            """Special target register for rshuffle iNTT auxiliary table."""
            return 2

        @classproperty
        def TARGET_iNTT_ROUTING_TABLE(cls):
            """Special target register for rshuffle iNTT routing table."""
            return 3


class MemoryModel:
    """
    Constants related to memory model.

    This class defines a hierarchical structure for different parts of the memory model,
    including queue capacities, metadata registers, and specific memory components like
    HBM and SPAD.
    """

    __XINST_QUEUE_MAX_CAPACITY: int
    __CINST_QUEUE_MAX_CAPACITY: int
    __MINST_QUEUE_MAX_CAPACITY: int
    __STORE_BUFFER_MAX_CAPACITY: int

    # Class-level attributes
    __NUM_BLOCKS_PER_TWID_META_WORD: int
    __NUM_BLOCKS_PER_KGSEED_META_WORD: int
    __NUM_ROUTING_TABLE_REGISTERS: int
    __NUM_ONES_META_REGISTERS: int
    __NUM_TWIDDLE_META_REGISTERS: int
    __TWIDDLE_META_REGISTER_SIZE_BYTES: int
    __MAX_RESIDUALS: int
    __NUM_REGISTER_BANKS: int
    __NUM_REGISTERS_PER_BANK: int

    @classproperty
    def XINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the XINST queue in bytes."""
        return cls.__XINST_QUEUE_MAX_CAPACITY

    @classproperty
    def XINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the XINST queue in words."""
        return convertBytes2Words(cls.__XINST_QUEUE_MAX_CAPACITY)

    @classproperty
    def CINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the CINST queue in bytes."""
        return cls.__CINST_QUEUE_MAX_CAPACITY

    @classproperty
    def CINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the CINST queue in words."""
        return convertBytes2Words(cls.__CINST_QUEUE_MAX_CAPACITY)

    @classproperty
    def MINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the MINST queue in bytes."""
        return cls.__MINST_QUEUE_MAX_CAPACITY

    @classproperty
    def MINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the MINST queue in words."""
        return convertBytes2Words(cls.__MINST_QUEUE_MAX_CAPACITY)

    @classproperty
    def STORE_BUFFER_MAX_CAPACITY(cls):
        """Maximum capacity of the store buffer in bytes."""
        return cls.__STORE_BUFFER_MAX_CAPACITY

    @classproperty
    def STORE_BUFFER_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the store buffer in words."""
        return convertBytes2Words(cls.__STORE_BUFFER_MAX_CAPACITY)

    @classproperty
    def NUM_BLOCKS_PER_TWID_META_WORD(cls) -> int:
        """Number of blocks per twiddle metadata word."""
        return cls.__NUM_BLOCKS_PER_TWID_META_WORD

    @classproperty
    def NUM_BLOCKS_PER_KGSEED_META_WORD(cls) -> int:
        """Number of blocks per key generation seed metadata word."""
        return cls.__NUM_BLOCKS_PER_KGSEED_META_WORD

    @classproperty
    def NUM_ROUTING_TABLE_REGISTERS(cls) -> int:
        """
        Number of routing table registers.

        This affects how many rshuffle of different types can be performed
        at the same time, since rshuffle instructions will pick a routing table
        to use to compute the shuffled result.
        """
        return cls.__NUM_ROUTING_TABLE_REGISTERS

    @classproperty
    def NUM_ONES_META_REGISTERS(cls) -> int:
        """
        Number of registers to hold identity metadata.

        This directly affects the maximum number of residuals that can be
        processed in the CE without needing to load new metadata.
        """
        return cls.__NUM_ONES_META_REGISTERS

    @classproperty
    def NUM_TWIDDLE_META_REGISTERS(cls) -> int:
        """
        Number of registers to hold twiddle factor metadata.

        This directly affects the maximum number of residuals that can be
        processed in the CE without needing to load new metadata.
        """
        return cls.__NUM_TWIDDLE_META_REGISTERS

    @classproperty
    def TWIDDLE_META_REGISTER_SIZE_BYTES(cls) -> int:
        """
        Size, in bytes, of a twiddle factor metadata register.
        """
        return cls.__TWIDDLE_META_REGISTER_SIZE_BYTES

    @classproperty
    def MAX_RESIDUALS(cls) -> int:
        """
        Maximum number of residuals that can be processed in the CE without
        needing to load new metadata.
        """
        return cls.__MAX_RESIDUALS

    @classproperty
    def NUM_REGISTER_BANKS(cls) -> int:
        """Number of register banks in the CE"""
        return cls.__NUM_REGISTER_BANKS

    @classproperty
    def NUM_REGISTERS_PER_BANK(cls) -> int:
        """Number of register per register banks in the CE"""
        return cls.__NUM_REGISTERS_PER_BANK

    @classmethod
    def hw_spec_as_dict(cls) -> dict:
        """
        Returns hw configurable attributes as dictionary.
        """
        return {
            "max_xinst_queue_size_in_bytes": cls.__XINST_QUEUE_MAX_CAPACITY,
            "max_cinst_queue_size_in_bytes": cls.__CINST_QUEUE_MAX_CAPACITY,
            "max_minst_queue_size_in_bytes": cls.__MINST_QUEUE_MAX_CAPACITY,
            "max_store_buffer_size_in_bytes": cls.__STORE_BUFFER_MAX_CAPACITY,
            "num_blocks_per_twid_meta_word": cls.NUM_BLOCKS_PER_TWID_META_WORD,
            "num_blocks_per_kgseed_meta_word": cls.NUM_BLOCKS_PER_KGSEED_META_WORD,
            "num_routing_table_registers": cls.NUM_ROUTING_TABLE_REGISTERS,
            "num_ones_meta_registers": cls.NUM_ONES_META_REGISTERS,
            "num_twiddle_meta_registers": cls.NUM_TWIDDLE_META_REGISTERS,
            "twiddle_meta_register_size_in_bytes": cls.TWIDDLE_META_REGISTER_SIZE_BYTES,
            "max_residuals": cls.MAX_RESIDUALS,
            "num_register_banks": cls.NUM_REGISTER_BANKS,
            "num_registers_per_bank": cls.NUM_REGISTERS_PER_BANK,
        }

    @classmethod
    def setMaxXInstQueueCapacity(cls, val: int):
        """
        Sets max XInst queue capacity
        """
        cls.__XINST_QUEUE_MAX_CAPACITY = val

    @classmethod
    def setMaxCInstQueueCapacity(cls, val: int):
        """
        Sets max CInst queue capacity
        """
        cls.__CINST_QUEUE_MAX_CAPACITY = val

    @classmethod
    def setMaxMInstQueueCapacity(cls, val: int):
        """
        Sets max MInst queue capacity
        """
        cls.__MINST_QUEUE_MAX_CAPACITY = val

    @classmethod
    def setMaxStoreBufferCapacity(cls, val: int):
        """
        Sets max store buffer capacity
        """
        cls.__STORE_BUFFER_MAX_CAPACITY = val

    @classmethod
    def setNumBlocksPerTwidMetaWord(cls, val: int):
        """
        Sets the number of blocks per twiddle metadata word.
        """
        cls.__NUM_BLOCKS_PER_TWID_META_WORD = val

    @classmethod
    def setNumBlocksPerKgseedMetaWord(cls, val: int):
        """
        Sets the number of blocks per key generation seed metadata word.
        """
        cls.__NUM_BLOCKS_PER_KGSEED_META_WORD = val

    @classmethod
    def setNumRoutingTableRegisters(cls, val: int):
        """
        Sets the number of routing table registers.
        """
        cls.__NUM_ROUTING_TABLE_REGISTERS = val

    @classmethod
    def setNumOnesMetaRegisters(cls, val: int):
        """
        Sets the number of ones metadata registers.
        """
        cls.__NUM_ONES_META_REGISTERS = val

    @classmethod
    def setNumTwiddleMetaRegisters(cls, val: int):
        """
        Sets the number of twiddle metadata registers.
        """
        cls.__NUM_TWIDDLE_META_REGISTERS = val

    @classmethod
    def setTwiddleMetaRegisterSizeBytes(cls, val: int):
        """
        Sets the size of twiddle metadata register in bytes.
        """
        cls.__TWIDDLE_META_REGISTER_SIZE_BYTES = val

    @classmethod
    def setMaxResiduals(cls, val: int):
        """
        Sets the maximum number of residuals.
        """
        cls.__MAX_RESIDUALS = val

    @classmethod
    def setNumRegisterBanks(cls, val: int):
        """
        Sets the number of register banks.
        """
        cls.__NUM_REGISTER_BANKS = val

    @classmethod
    def setNumRegistersPerBank(cls, val: int):
        """
        Sets the number of registers per bank.
        """
        cls.__NUM_REGISTERS_PER_BANK = val

    class HBM:
        """
        Constants related to High Bandwidth Memory (HBM).

        This class defines the maximum capacity of HBM in both bytes and words.
        """

        __MAX_CAPACITY: int

        @classproperty
        def MAX_CAPACITY(cls) -> int:
            """Total capacity of HBM in Bytes"""
            return cls.__MAX_CAPACITY

        @classproperty
        def MAX_CAPACITY_WORDS(cls) -> int:
            """Total capacity of HBM in Words"""
            return convertBytes2Words(cls.__MAX_CAPACITY)

        @classmethod
        def hw_spec_as_dict(cls) -> dict:
            """
            Returns hw configurable attributes as dictionary.
            """
            return {"max_hbm_size_in_bytes": cls.__MAX_CAPACITY}

        @classmethod
        def setMaxCapacity(cls, val: int):
            """
            Sets max SPAD Capacity
            """
            cls.__MAX_CAPACITY = val

    class SPAD:
        """
        Constants related to Scratchpad Memory (SPAD).

        This class defines the maximum capacity of SPAD in both bytes and words.
        """

        __MAX_CAPACITY: int

        # Class methods and properties
        # ----------------------------

        @classproperty
        def MAX_CAPACITY(cls) -> int:
            """Total capacity of SPAD in Bytes"""
            return cls.__MAX_CAPACITY

        @classproperty
        def MAX_CAPACITY_WORDS(cls) -> int:
            """Total capacity of SPAD in Words"""
            return convertBytes2Words(cls.__MAX_CAPACITY)

        @classmethod
        def hw_spec_as_dict(cls) -> dict:
            """
            Returns hw configurable attributes as dictionary.
            """
            return {"max_cache_size_in_bytes": cls.__MAX_CAPACITY}

        @classmethod
        def setMaxCapacity(cls, val: int):
            """
            Sets max SPAD Capacity
            """
            cls.__MAX_CAPACITY = val
