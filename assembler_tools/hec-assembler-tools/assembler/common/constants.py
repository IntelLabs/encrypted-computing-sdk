
from .decorators import *

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
       return ( cls.REPLACEMENT_POLICY_FTBU, cls.REPLACEMENT_POLICY_LRU )

    # Misc Constants
    # --------------

    @classproperty
    def XINSTRUCTION_SIZE_BYTES(cls) -> int:
        """Size of an x-instruction in bytes."""
        return 8

    @classproperty
    def MAX_BUNDLE_SIZE(cls) -> int:
        """Maximum number of instructions in a bundle."""
        return 64

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
        return [ "add", "mul", "ntt", "intt", "relin", "mod_switch", "rotate",
                 "square", "add_plain", "add_corrected", "mul_plain", "rescale",
                 "boot_dot_prod", "boot_mod_drop_scale", "boot_mul_const", "boot_galois_plain" ]

def convertBytes2Words(bytes: int) -> int:
    """
    Converts a size in bytes to the equivalent number of words.

    Args:
        bytes (int): The size in bytes to be converted.

    Returns:
        int: The equivalent size in words.
    """
    return int(bytes / Constants.WORD_SIZE)

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
        return ( cls.MetaFields.FIELD_KEYGEN_SEED,
                 cls.MetaFields.FIELD_TWIDDLE,
                 cls.MetaFields.FIELD_ONES,
                 cls.MetaFields.FIELD_NTT_AUX_TABLE,
                 cls.MetaFields.FIELD_NTT_ROUTING_TABLE,
                 cls.MetaFields.FIELD_iNTT_AUX_TABLE,
                 cls.MetaFields.FIELD_iNTT_ROUTING_TABLE )

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

    __XINST_QUEUE_MAX_CAPACITY = 1 * Constants.MEGABYTE
    __XINST_QUEUE_MAX_CAPACITY_WORDS = convertBytes2Words(__XINST_QUEUE_MAX_CAPACITY)
    __CINST_QUEUE_MAX_CAPACITY = 128 * Constants.KILOBYTE
    __CINST_QUEUE_MAX_CAPACITY_WORDS = convertBytes2Words(__CINST_QUEUE_MAX_CAPACITY)
    __MINST_QUEUE_MAX_CAPACITY = 128 * Constants.KILOBYTE
    __MINST_QUEUE_MAX_CAPACITY_WORDS = convertBytes2Words(__MINST_QUEUE_MAX_CAPACITY)
    __STORE_BUFFER_MAX_CAPACITY = 128 * Constants.KILOBYTE
    __STORE_BUFFER_MAX_CAPACITY_WORDS = convertBytes2Words(__STORE_BUFFER_MAX_CAPACITY)

    @classproperty
    def XINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the XINST queue in bytes."""
        return cls.__XINST_QUEUE_MAX_CAPACITY
    @classproperty
    def XINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the XINST queue in words."""
        return cls.__XINST_QUEUE_MAX_CAPACITY_WORDS
    @classproperty
    def CINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the CINST queue in bytes."""
        return cls.__CINST_QUEUE_MAX_CAPACITY
    @classproperty
    def CINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the CINST queue in words."""
        return cls.__CINST_QUEUE_MAX_CAPACITY_WORDS
    @classproperty
    def MINST_QUEUE_MAX_CAPACITY(cls):
        """Maximum capacity of the MINST queue in bytes."""
        return cls.__MINST_QUEUE_MAX_CAPACITY
    @classproperty
    def MINST_QUEUE_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the MINST queue in words."""
        return cls.__MINST_QUEUE_MAX_CAPACITY_WORDS
    @classproperty
    def STORE_BUFFER_MAX_CAPACITY(cls):
        """Maximum capacity of the store buffer in bytes."""
        return cls.__STORE_BUFFER_MAX_CAPACITY
    @classproperty
    def STORE_BUFFER_MAX_CAPACITY_WORDS(cls):
        """Maximum capacity of the store buffer in words."""
        return cls.__STORE_BUFFER_MAX_CAPACITY_WORDS

    @classproperty
    def NUM_BLOCKS_PER_TWID_META_WORD(cls) -> int:
        """Number of blocks per twiddle metadata word."""
        return 4

    @classproperty
    def NUM_BLOCKS_PER_KGSEED_META_WORD(cls) -> int:
        """Number of blocks per key generation seed metadata word."""
        return 4

    @classproperty
    def NUM_ROUTING_TABLE_REGISTERS(cls) -> int:
        """
        Number of routing table registers.

        This affects how many rshuffle of different types can be performed
        at the same time, since rshuffle instructions will pick a routing table
        to use to compute the shuffled result.
        """
        return 1

    @classproperty
    def NUM_ONES_META_REGISTERS(cls) -> int:
        """
        Number of registers to hold identity metadata.

        This directly affects the maximum number of residuals that can be
        processed in the CE without needing to load new metadata.
        """
        return 1

    @classproperty
    def NUM_TWIDDLE_META_REGISTERS(cls) -> int:
        """
        Number of registers to hold twiddle factor metadata.

        This directly affects the maximum number of residuals that can be
        processed in the CE without needing to load new metadata.
        """
        return 32 * cls.NUM_ONES_META_REGISTERS

    @classproperty
    def TWIDDLE_META_REGISTER_SIZE_BYTES(cls) -> int:
        """
        Size, in bytes, of a twiddle factor metadata register.
        """
        return 8 * Constants.KILOBYTE

    @classproperty
    def MAX_RESIDUALS(cls) -> int:
        """
        Maximum number of residuals that can be processed in the CE without
        needing to load new metadata.
        """
        return cls.NUM_TWIDDLE_META_REGISTERS * 2

    @classproperty
    def NUM_REGISTER_BANKS(cls) -> int:
        """Number of register banks in the CE"""
        return 4

    @classproperty
    def NUM_REGISTER_PER_BANKS(cls) -> int:
        """Number of register per register banks in the CE"""
        return 72

    class HBM:
        """
        Constants related to High Bandwidth Memory (HBM).

        This class defines the maximum capacity of HBM in both bytes and words.
        """
        __MAX_CAPACITY = 64 * Constants.GIGABYTE
        __MAX_CAPACITY_WORDS = convertBytes2Words(__MAX_CAPACITY)

        @classproperty
        def MAX_CAPACITY(cls) -> int:
            """Total capacity of HBM in Bytes"""
            return cls.__MAX_CAPACITY

        @classproperty
        def MAX_CAPACITY_WORDS(cls) -> int:
            """Total capacity of HBM in Words"""
            return cls.__MAX_CAPACITY_WORDS

    class SPAD:
        """
        Constants related to Scratchpad Memory (SPAD).

        This class defines the maximum capacity of SPAD in both bytes and words.
        """
        __MAX_CAPACITY = 64 * Constants.MEGABYTE
        __MAX_CAPACITY_WORDS = convertBytes2Words(__MAX_CAPACITY)

        # Class methods and properties
        # ----------------------------

        @classproperty
        def MAX_CAPACITY(cls) -> int:
            """Total capacity of SPAD in Bytes"""
            return cls.__MAX_CAPACITY

        @classproperty
        def MAX_CAPACITY_WORDS(cls) -> int:
            """Total capacity of SPAD in Words"""
            return cls.__MAX_CAPACITY_WORDS
