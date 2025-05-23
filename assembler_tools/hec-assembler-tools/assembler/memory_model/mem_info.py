from assembler.common import constants
from assembler.instructions import tokenizeFromLine
from assembler.memory_model.variable import Variable
from . import MemoryModel

class MemInfoVariable:
    """
    Represents a memory information variable with a name and an HBM address.

    This class encapsulates the details of a variable, including its name and the
    address in high-bandwidth memory (HBM) where it is stored.
    """
    def __init__(self,
                 var_name: str,
                 hbm_address: int):
        """
        Initializes a new MemInfoVariable object with a specified name and HBM address.

        Args:
            var_name (str): The name of the variable. Must be a valid identifier.
            hbm_address (int): The HBM address where the variable is stored.

        Raises:
            RuntimeError: If the variable name is invalid.
        """
        if not Variable.validateName(var_name):
            raise RuntimeError(f'Invalid variable name "{var_name}"')
        self.var_name = var_name.strip()
        self.hbm_address = hbm_address

    def __repr__(self):
        """
        Returns a string representation of the MemInfoVariable object.

        Returns:
            str: A string representation of the object as a dictionary.
        """
        return repr(self.as_dict())

    def as_dict(self) -> dict:
        """
        Converts the MemInfoVariable object to a dictionary.

        Returns:
            dict: A dictionary representation of the variable, including its name and HBM address.
        """
        return { 'var_name': self.var_name,
                 'hbm_address': self.hbm_address }

class MemInfoKeygenVariable(MemInfoVariable):
    """
    Represents a memory information key generation variable.

    This class extends MemInfoVariable to include additional attributes for key generation,
    specifically the seed index and key index associated with the variable.
    """
    def __init__(self,
                 var_name: str,
                 seed_index: int,
                 key_index: int):
        """
        Initializes a new MemInfoKeygenVariable object with a specified name, seed index, and key index.

        Args:
            var_name (str): The name of the variable. Must be a valid identifier.
            seed_index (int): The index of the seed used for key generation. Must be a zero-based index.
            key_index (int): The index of the key. Must be a zero-based index.

        Raises:
            IndexError: If the seed index or key index is negative.
        """
        super().__init__(var_name, -1)
        if seed_index < 0:
            raise IndexError('seed_index: must be a zero-based index.')
        if key_index < 0:
            raise IndexError('key_index: must be a zero-based index.')
        self.seed_index = seed_index
        self.key_index  = key_index

    def as_dict(self) -> dict:
        """
        Converts the MemInfoKeygenVariable object to a dictionary.

        Returns:
            dict: A dictionary representation of the variable, including its name, seed index, and key index.
        """
        return { 'var_name': self.var_name,
                 'seed_index': self.seed_index,
                 'key_index': self.key_index }

class MemInfo:
    """
    Represents memory information for a set of variables and metadata fields.

    This class encapsulates the parsing and management of memory information variables,
    including key generation variables, input and output variables, and various metadata fields.
    """

    Const = constants.MemInfo

    class Metadata:
        """
        Encapsulates metadata fields within the memory information.

        This class provides methods for parsing and accessing metadata variables such as
        ones, NTT auxiliary tables, NTT routing tables, iNTT auxiliary tables, iNTT routing tables,
        twiddle factors, and keygen seeds.
        """

        class Ones:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses a ones metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed ones metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_ONES,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_ONES)

        class NTTAuxTable:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses an NTT auxiliary table metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed NTT auxiliary table metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_NTT_AUX_TABLE,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_NTT_AUX_TABLE)

        class NTTRoutingTable:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses an NTT routing table metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed NTT routing table metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_NTT_ROUTING_TABLE,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_NTT_ROUTING_TABLE)

        class iNTTAuxTable:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses an iNTT auxiliary table metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed iNTT auxiliary table metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_iNTT_AUX_TABLE,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_iNTT_AUX_TABLE)

        class iNTTRoutingTable:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses an iNTT routing table metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed iNTT routing table metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_iNTT_ROUTING_TABLE,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_iNTT_ROUTING_TABLE)

        class Twiddle:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses a twiddle metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed twiddle metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_TWIDDLE,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_TWIDDLE)

        class KeygenSeed:
            @classmethod
            def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
                """
                Parses a keygen seed metadata variable from a tokenized line.

                Args:
                    tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

                Returns:
                    MemInfoVariable: The parsed keygen seed metadata variable.
                """
                return MemInfo.Metadata.parseMetaFieldFromMemLine(tokens,
                                                                  MemInfo.Const.Keyword.LOAD_KEYGEN_SEED,
                                                                  var_prefix=MemInfo.Const.Keyword.LOAD_KEYGEN_SEED)

        @classmethod
        def parseMetaFieldFromMemLine(cls,
                                      tokens: list,
                                      meta_field_name: str,
                                      var_prefix: str = "meta",
                                      var_extra: str = None) -> MemInfoVariable:
            """
            Parses a metadata variable name from a tokenized line.

            Args:
                tokens (list[str]): Fully tokenized line from which to parse. Expected format: `dload, <meta_field_name>, <hbm_addr: int> [, var_name]`.
                meta_field_name (str): Name identifying the meta field to parse from the tokens.
                var_prefix (str, optional): Prefix for the metadata variable. Ignored if a name is supplied in the tokens.
                var_extra (str, optional): Extra postfix to add to the variable name. Ignored if a name is supplied in the tokens.

            Returns:
                MemInfoVariable: The mem info for the parsed variable, or None if no variable could be parsed.
            """
            retval = None
            if len(tokens) >= 3:
                if tokens[0] == MemInfo.Const.Keyword.LOAD \
                    and tokens[1] == meta_field_name:
                    hbm_addr = int(tokens[2])
                    if len(tokens) >= 4 and tokens[3]:
                        # name supplied in the tokenized line
                        var_name = tokens[3]
                    else:
                        if var_extra is None:
                            var_extra = f'_{hbm_addr}'
                        else:
                            var_extra = var_extra.strip()
                        var_name = f'{var_prefix}{var_extra}'
                    retval = MemInfoVariable(var_name = var_name,
                                             hbm_address = hbm_addr)
            return retval

        def __init__(self, **kwargs):
            """
            Initializes a new Metadata object with specified metadata fields.

            Args:
                kwargs (dict): A dictionary containing metadata fields and their corresponding MemInfoVariable objects.
            """
            self.__meta_dict = {}
            for meta_field in MemInfo.Const.FIELD_METADATA_SUBFIELDS:
                self.__meta_dict[meta_field] = [ MemInfoVariable(**d) for d in kwargs.get(meta_field, []) ]

        def __getitem__(self, key):
            """
            Retrieves the list of MemInfoVariable objects for the specified metadata field.

            Args:
                key: The metadata field key.

            Returns:
                list: A list of MemInfoVariable objects.
            """
            return self.__meta_dict[key]


        @property
        def ones(self) -> list:
            """
            Retrieves the list of ones metadata variables.

            Returns:
                list: Ones metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_ONES]

        @property
        def ntt_auxiliary_table(self) -> list:
            """
            Retrieves the list of NTT auxiliary table metadata variables.

            Returns:
                list: Metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_NTT_AUX_TABLE]

        @property
        def ntt_routing_table(self) -> list:
            """
            Retrieves the list of NTT routing table metadata variables.

            Returns:
                list: Metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_NTT_ROUTING_TABLE]

        @property
        def intt_auxiliary_table(self) -> list:
            """
            Retrieves the list of iNTT auxiliary table metadata variables.

            Returns:
                list: Metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_iNTT_AUX_TABLE]

        @property
        def intt_routing_table(self) -> list:
            """
            Retrieves the list of iNTT routing table metadata variables.

            Returns:
                list: Metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_iNTT_ROUTING_TABLE]

        @property
        def twiddle(self) -> list:
            """
            Retrieves the list of twiddle metadata variables.

            Returns:
                list: Twiddle metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_TWIDDLE]

        @property
        def keygen_seeds(self) -> list:
            """
            Retrieves the list of keygen seed metadata variables.

            Returns:
                list: Keygen seed metadata variables.
            """
            return self.__meta_dict[MemInfo.Const.MetaFields.FIELD_KEYGEN_SEED]

    class Keygen:
        @classmethod
        def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
            """
            Parses a keygen variable from a tokenized line.

            Args:
                tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

            Returns:
                MemInfoKeygenVariable: Mem Info describing a keygen variable.
            """
            retval = None
            if len(tokens) >= 4:
                if tokens[0] == MemInfo.Const.Keyword.KEYGEN:
                    seed_idx = int(tokens[1])
                    key_idx  = int(tokens[2])
                    var_name = tokens[3]
                    retval = MemInfoKeygenVariable(var_name = var_name,
                                                   seed_index = seed_idx,
                                                   key_index = key_idx)
            return retval

    class Input:
        @classmethod
        def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
            """
            Parses an input variable from a tokenized line.

            Args:
                tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

            Returns:
                MemInfoVariable: The parsed input variable.
            """
            retval = None
            if len(tokens) >= 4:
                if tokens[0] == MemInfo.Const.Keyword.LOAD \
                    and tokens[1] == MemInfo.Const.Keyword.LOAD_INPUT:
                    hbm_addr = int(tokens[2])
                    var_name = tokens[3]
                    if Variable.validateName(var_name):
                        retval = MemInfoVariable(var_name = var_name,
                                                 hbm_address = hbm_addr)
            return retval

    class Output:
        @classmethod
        def parseFromMemLine(cls, tokens: list) -> MemInfoVariable:
            """
            Parses an output variable from a tokenized line.

            Args:
                tokens (list[str]): Fully tokenized line to parse from. This must include all tokens, including the initial keyword.

            Returns:
                MemInfoVariable: The parsed output variable.
            """
            retval = None
            if len(tokens) >= 3:
                if tokens[0] == MemInfo.Const.Keyword.STORE:
                    hbm_addr = int(tokens[2])
                    var_name = tokens[1]
                    if Variable.validateName(var_name):
                        retval = MemInfoVariable(var_name = var_name,
                                                 hbm_address = hbm_addr)
            return retval

    def __init__(self, **kwargs):
        """
        Initializes a new MemInfo object.

        Clients may call this method without parameters for default initialization.
        Clients should use MemInfo.from_iter() constructor to parse the contents of a .mem file.

        Args:
            kwargs (dict): A dictionary as generated by the method MemInfo.as_dict(). This is provided as
            a shortcut to creating a MemInfo object from structured data such as the contents of a YAML file.
        """
        self.__keygens  = [ MemInfoVariable(**d) for d in kwargs.get(MemInfo.Const.FIELD_KEYGENS, []) ]
        self.__inputs   = [ MemInfoVariable(**d) for d in kwargs.get(MemInfo.Const.FIELD_INPUTS, []) ]
        self.__outputs  = [ MemInfoVariable(**d) for d in kwargs.get(MemInfo.Const.FIELD_OUTPUTS, []) ]
        self.__metadata = MemInfo.Metadata(**kwargs.get(MemInfo.Const.FIELD_METADATA, {}))
        self.validate()

    @classmethod
    def from_iter(cls, line_iter):
        """
        Creates a new MemInfo object from an iterator of strings, where each string is a line of text to parse.

        This constructor is intended to parse a .mem file.

        Args:
            line_iter (iter): Iterator of strings. Each string is considered a line of text to parse.

        Raises:
            RuntimeError: If there is an error parsing the lines.

        Returns:
            MemInfo: The constructed MemInfo object.
        """

        retval = cls()

        factory_dict = { MemInfo.Keygen: retval.keygens,
                         MemInfo.Input: retval.inputs,
                         MemInfo.Output: retval.outputs,
                         MemInfo.Metadata.KeygenSeed: retval.metadata.keygen_seeds,
                         MemInfo.Metadata.Ones: retval.metadata.ones,
                         MemInfo.Metadata.NTTAuxTable: retval.metadata.ntt_auxiliary_table,
                         MemInfo.Metadata.NTTRoutingTable: retval.metadata.ntt_routing_table,
                         MemInfo.Metadata.iNTTAuxTable: retval.metadata.intt_auxiliary_table,
                         MemInfo.Metadata.iNTTRoutingTable: retval.metadata.intt_routing_table,
                         MemInfo.Metadata.Twiddle: retval.metadata.twiddle }
        for line_no, s_line in enumerate(line_iter, 1):
            s_line = s_line.strip()
            if s_line: # skip empty lines
                tokens, _ = tokenizeFromLine(s_line)
                if tokens and len(tokens) > 0:
                    b_parsed = False
                    for mem_info_type in factory_dict:
                        miv: MemInfoVariable = mem_info_type.parseFromMemLine(tokens)
                        if miv is not None:
                            factory_dict[mem_info_type].append(miv)
                            b_parsed = True
                            break # next line
                    if not b_parsed:
                        raise RuntimeError(f'Could not parse line {line_no}: "{s_line}"')
        retval.validate()
        return retval

    @property
    def keygens(self) -> list:
        """
        Retrieves the list of keygen variables.

        Returns:
            list: Keygen variables.
        """
        return self.__keygens

    @property
    def inputs(self) -> list:
        """
        Retrieves the list of input variables.

        Returns:
            list: Input variables.
        """
        return self.__inputs

    @property
    def outputs(self) -> list:
        """
        Retrieves the list of output variables.

        Returns:
            list: Output variables.
        """
        return self.__outputs

    @property
    def metadata(self) -> Metadata:
        """
        Retrieves the metadata associated with this MemInfo object.

        Returns:
            Metadata: MemInfo's metadata.
        """
        return self.__metadata

    def as_dict(self):
        """
        Returns a dictionary representation of this MemInfo object.

        Returns:
            dict: A dictionary representation of the MemInfo object.
        """
        return { MemInfo.Const.FIELD_KEYGENS: [ x.as_dict() for x in self.keygens ],
                 MemInfo.Const.FIELD_INPUTS: [ x.as_dict() for x in self.inputs ],
                 MemInfo.Const.FIELD_OUTPUTS: [ x.as_dict() for x in self.outputs ],
                 MemInfo.Const.FIELD_METADATA: { meta_field: [ x.as_dict() for x in self.metadata[meta_field] ] \
                                                for meta_field in MemInfo.Const.FIELD_METADATA_SUBFIELDS if self.metadata[meta_field] } }

    def validate(self):
        """
        Validates the MemInfo object to ensure consistency and correctness.

        Raises:
            RuntimeError: If the validation fails due to inconsistent metadata or duplicate variable names.
        """
        if len(self.metadata.ones) * MemoryModel.MAX_TWIDDLE_META_VARS_PER_SEGMENT != len(self.metadata.twiddle):
            raise RuntimeError(('Expected {} times as many twiddles as ones metadata values, '
                                'but received {} twiddles and {} ones.').format(MemoryModel.MAX_TWIDDLE_META_VARS_PER_SEGMENT,
                                                                                len(self.metadata.twiddle),
                                                                                len(self.metadata.ones)))
        # Avoid duplicate variable names with different HBM addresses.
        mem_info_vars = {}
        all_var_info = self.inputs + self.outputs \
                       + self.metadata.intt_auxiliary_table + self.metadata.intt_routing_table \
                       + self.metadata.ntt_auxiliary_table + self.metadata.ntt_routing_table \
                       + self.metadata.ones + self.metadata.twiddle
        for var_info in all_var_info:
            if var_info.var_name not in mem_info_vars:
                mem_info_vars[var_info.var_name] = var_info
            elif mem_info_vars[var_info.var_name].hbm_address != var_info.hbm_address:
                raise RuntimeError(('Variable "{}" already allocated in HBM address {}, '
                                    'but new allocation requested into address {}.').format(var_info.var_name,
                                                                                            mem_info_vars[var_info.var_name].hbm_address,
                                                                                            var_info.hbm_address))

def __allocateMemInfoVariable(mem_model: MemoryModel,
                              v_info: MemInfoVariable):
    """
    Allocates a memory information variable in the memory model.

    This function ensures that the specified variable is allocated in the high-bandwidth memory (HBM)
    of the memory model. It checks if the variable is present in the memory model and allocates it
    at the specified HBM address if it is not already allocated.

    Args:
        mem_model (MemoryModel): The memory model in which to allocate the variable.
        v_info (MemInfoVariable): The memory information variable to allocate.

    Raises:
        RuntimeError: If the variable is not present in the memory model or if there is a conflicting
        allocation request.
    """
    assert v_info.hbm_address >= 0
    if v_info.var_name not in mem_model.variables:
        raise RuntimeError(f'Variable {v_info.var_name} not in memory model. All variables used in mem info must be present in P-ISA kernel.')
    if mem_model.variables[v_info.var_name].hbm_address < 0:
        mem_model.hbm.allocateForce(v_info.hbm_address, mem_model.variables[v_info.var_name])
    elif v_info.hbm_address != mem_model.variables[v_info.var_name].hbm_address:
        raise RuntimeError(('Variable {} already allocated in HBM address {}, '
                            'but new allocation requested into address {}.').format(v_info.var_name,
                                                                                    mem_model.variables[v_info.var_name].hbm_address,
                                                                                    v_info.hbm_address))

def updateMemoryModelWithMemInfo(mem_model: MemoryModel,
                                 mem_info: MemInfo):
    """
    Updates the memory model with memory information.

    This function updates the memory model by allocating variables and metadata fields
    specified in the memory information. It processes inputs, outputs, metadata, and keygen
    variables, ensuring they are correctly allocated and added to the memory model.

    Args:
        mem_model (MemoryModel): The memory model to update.
        mem_info (MemInfo): The memory information containing variables and metadata to allocate.

    Raises:
        RuntimeError: If there are inconsistencies or errors during the allocation process.
    """

    # Inputs
    for v_info in mem_info.inputs:
        __allocateMemInfoVariable(mem_model, v_info)

    # Outputs
    for v_info in mem_info.outputs:
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.output_variables.push(v_info.var_name, None)

    # Metadata

    # Ones
    for v_info in mem_info.metadata.ones:
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.add_meta_ones_var(v_info.var_name)

    # Shuffle meta vars
    if mem_info.metadata.ntt_auxiliary_table:
        assert(len(mem_info.metadata.ntt_auxiliary_table) == 1)
        v_info = mem_info.metadata.ntt_auxiliary_table[0]
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.meta_ntt_aux_table = v_info.var_name

    if mem_info.metadata.ntt_routing_table:
        assert(len(mem_info.metadata.ntt_routing_table) == 1)
        v_info = mem_info.metadata.ntt_routing_table[0]
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.meta_ntt_routing_table = v_info.var_name

    if mem_info.metadata.intt_auxiliary_table:
        assert(len(mem_info.metadata.intt_auxiliary_table) == 1)
        v_info = mem_info.metadata.intt_auxiliary_table[0]
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.meta_intt_aux_table = v_info.var_name

    if mem_info.metadata.intt_routing_table:
        assert(len(mem_info.metadata.intt_routing_table) == 1)
        v_info = mem_info.metadata.intt_routing_table[0]
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.meta_intt_routing_table = v_info.var_name

    # Twiddle
    for v_info in mem_info.metadata.twiddle:
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.add_meta_twiddle_var(v_info.var_name)

    # Keygen seeds
    for v_info in mem_info.metadata.keygen_seeds:
        mem_model.retrieveVarAdd(v_info.var_name)
        __allocateMemInfoVariable(mem_model, v_info)
        mem_model.add_meta_keygen_seed_var(v_info.var_name)

    # End metadata

    # Keygen variables
    for v_info in mem_info.keygens:
        mem_model.add_keygen_variable(**v_info.as_dict())
