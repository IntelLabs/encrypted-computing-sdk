import os
import math
import pathlib
from typing import NamedTuple

from assembler.common import constants
from assembler.common.decorators import *
from assembler.common.queue_dict import QueueDict
from . import hbm
from . import spad
from . import register_file
from .variable import Variable
from .variable import findVarByName
from pickle import NONE

class MemoryModel:
    """
    Represents a memory model with various components such as HBM, SPAD, and register banks.

    This class provides methods and properties to manage and interact with different parts
    of the memory model, including metadata variables and output variables.
    """
    class StoreBufferValueType(NamedTuple):
        """
        Represents a value type for the store buffer.

        Attributes:
            variable (Variable): The variable associated with the store buffer entry.
            dest_spad_address (int): The destination SPAD address for the variable.
        """
        variable: Variable
        dest_spad_address: int

    __MAX_TWIDDLE_META_VARS_PER_SEGMENT = math.ceil(constants.MemoryModel.NUM_TWIDDLE_META_REGISTERS * \
                                                    constants.MemoryModel.TWIDDLE_META_REGISTER_SIZE_BYTES / \
                                                    constants.Constants.WORD_SIZE)

    @classproperty
    def MAX_TWIDDLE_META_VARS_PER_SEGMENT(cls):
        """
        Gets the number of variables needed to fill up the twiddle factor metadata registers.

        Returns:
            int: The number of variables per segment.
        """
        return cls.__MAX_TWIDDLE_META_VARS_PER_SEGMENT


    # Constructor
    # -----------

    def __init__(self,
                 hbm_capacity_words: int,
                 spad_capacity_words: int,
                 num_register_banks: int = constants.MemoryModel.NUM_REGISTER_BANKS,
                 register_range: range = None):
        """
        Initializes a new MemoryModel object.

        Args:
            hbm_capacity_words (int): The capacity of the HBM in words.
            spad_capacity_words (int): The capacity of the SPAD in words.
            num_register_banks (int, optional): The number of register banks. Defaults to constants.MemoryModel.NUM_REGISTER_BANKS.
            register_range (range, optional): A range for the indices of the registers contained in this register bank.
                Defaults to `range(constants.MemoryModel.NUM_REGISTER_PER_BANKS)`.

        Raises:
            ValueError: If the number of register banks is less than the required minimum.
        """
        # check that constant is correct
        assert self.MAX_TWIDDLE_META_VARS_PER_SEGMENT == 8

        if num_register_banks < constants.MemoryModel.NUM_REGISTER_BANKS:
            raise ValueError(('`num_register_banks`: there must be at least {} register banks, '
                              'but {} requested.').format(constants.MemoryModel.NUM_REGISTER_BANKS,
                                                          num_register_banks))
        self.__register_range = range(constants.MemoryModel.NUM_REGISTER_PER_BANKS) if not register_range else register_range
        # initialize members
        self.__store_buffer = QueueDict() # QueueDict(var_name: str, StoreBufferValueType)
        self.__variables = {} # dict(var_name, Variable)
        self.__meta_ones_vars = [] # list(QueueDict())
        self.meta_ntt_aux_table: str = "" # var name
        self.meta_ntt_routing_table: str = "" # var name
        self.meta_intt_aux_table: str = "" # var name
        self.meta_intt_routing_table: str = "" # var name
        self.__meta_twiddle_vars = [] # list(QueueDict())
        self.__meta_keygen_seed_vars = QueueDict() # QueueDict(var_name: str, None): set of variables that are seeds to this operation
        self.__keygen_vars = dict() # dict(var_name: str, tuple(seed_idx: int, key_idx: int)): set of variables that are output to this operation
        self.__output_vars = QueueDict() # QueueDict(var_name: str, None): set of variables that are output to this operation
        self.__last_keygen_order = (0, -1) # tracks the generation order of last keygen variable; next must be 1 above this order.
        self.__hbm = hbm.HBM(hbm_capacity_words)
        self.__spad = spad.SPAD(spad_capacity_words)
        self.__register_file = tuple([register_file.RegisterBank(idx, self.__register_range) \
            for idx in range(num_register_banks)])

    # Special Methods
    # ---------------

    def __repr__(self):
        """
        Returns a string representation of the MemoryModel object.

        Returns:
            str: The string representation.
        """
        retval = ('<{} object at {}>(hbm_capacity_words={}, '
                  'spad_capacity_words={}, '
                  'num_register_banks={}, '
                  'register_range={})').format(type(self).__name__,
                                               hex(id(self)),
                                               self.spad.CAPACITY_WORDS,
                                               self.hbm.CAPACITY_WORDS,
                                               len(self.reister_banks),
                                               self.__register_range)
        return retval


    # Methods and properties
    # ----------------------

    @property
    def hbm(self) -> hbm.HBM:
        """
        Gets the HBM component of the memory model.

        Returns:
            hbm.HBM: The HBM component.
        """
        return self.__hbm

    @property
    def spad(self) -> spad.SPAD:
        """
        Gets the SPAD component of the memory model.

        Returns:
            spad.SPAD: The SPAD component.
        """
        return self.__spad

    @property
    def store_buffer(self) -> QueueDict:
        """
        Gets the store buffer between SPAD and CE.

        Returns:
            QueueDict: QueueDict(var_name: str, StoreBufferValueType)
        """
        return self.__store_buffer

    @property
    def register_banks(self) -> tuple:
        """
        Gets the register banks in the memory model register file.

        Returns:
            tuple: A tuple of `RegisterBank` objects.
        """
        return self.__register_file

    @property
    def variables(self) -> dict:
        """
        Gets the dictionary of global variables, indexed by variable name.

        These are all the variables in the program. They may not be allocated in HBM. To
        check if they are allocated check the class:`Variable.hbm_address` property. It
        is allocated if greater than or equal to zero.

        Returns:
            dict: A dictionary of variables.
        """
        return self.__variables

    def add_meta_ones_var(self, var_name: str):
        """
        Marks an existing variable as Metadata Ones Variable.

        Args:
            var_name (str): The name of the variable to mark.

        Raises:
            RuntimeError: If the variable is not in the memory model.
        """
        if var_name not in self.variables:
            raise RuntimeError(f'Variable "{var_name}" is not in memory model.')
        self.__meta_ones_vars.append(QueueDict())
        self.__meta_ones_vars[-1].push(var_name, None)

    @property
    def meta_ones_vars_segments(self) -> list:
        """
        Retrieves the set of variable names that have been marked as Metadata Ones variables.
            
        A list of segments (list[QueueDict(str, None)]), where each segment is 
        the set of variable names that have been marked as Metadata Ones variables. 
        The size of each set is given by the number of variables needed to fill up 
        the ones metadata registers (see constants.MemoryModel.NUM_ONES_META_REGISTERS).
        Clients should not change these values. Use add_meta_ones_var() to add new ones metadata.
        
        Returns:
            list: A list of segments, each containing variable names.

        """
        return self.__meta_ones_vars

    def add_meta_twiddle_var(self, var_name: str):
        """
        Marks an existing variable as a twiddle metadata variable.

        Args:
            var_name (str): The name of the variable to mark.

        Raises:
            RuntimeError: If the variable is not in the memory model.
        """
        if var_name not in self.variables:
            raise RuntimeError(f'Variable "{var_name}" is not in memory model.')
        # Twiddle metadata variables are grouped in segments of 8
        if len(self.__meta_twiddle_vars) <= 0 \
           or len(self.__meta_twiddle_vars[-1]) >= self.MAX_TWIDDLE_META_VARS_PER_SEGMENT:
            self.__meta_twiddle_vars.append(QueueDict())
        self.__meta_twiddle_vars[-1].push(var_name, None)

    @property
    def meta_twiddle_vars_segments(self) -> list:
        """
        Gets the variable names that have been marked as Metadata Twiddle variables.

        Clients should not change these values. Use meta_twiddle_vars_segments() to add
        new twiddle metadata.
        
        A list of segments (list[QueueDict(str, None)]), where each segment is a set of
        variable names that have been marked as Metadata Twiddle variables. The size
        of each set is given by the number of variables needed to fill up the twiddle
        factor metadata registers (see MemoryModel.MAX_TWIDDLE_META_VARS_PER_SEGMENT).

        Returns:
            list: A list of segments containing variable names.
        """
        return self.__meta_twiddle_vars

    def isMetaVar(self, var_name: str) -> bool:
        """
        Checks whether a variable name is one of the meta variables.

        Args:
            var_name (str): The name of the variable to check.

        Returns:
            bool: True if the variable is a meta variable, False otherwise.
        """
        return bool(var_name) and \
           (var_name in self.meta_keygen_seed_vars \
         or any(var_name in meta_twiddle_vars for meta_twiddle_vars in self.meta_twiddle_vars_segments) \
         or any(var_name in meta_ones_vars for meta_ones_vars in self.meta_ones_vars_segments) \
         or var_name in set((self.meta_ntt_aux_table, self.meta_ntt_routing_table,
                             self.meta_intt_aux_table, self.meta_intt_routing_table)))

    @property
    def output_variables(self) -> QueueDict:
        """
        Gets the set of variable names that have been marked as output variables.

        Returns:
            QueueDict: The set of output variable names.
        """
        return self.__output_vars

    def add_meta_keygen_seed_var(self, var_name: str):
        """
        Marks an existing variable as a keygen seed.

        Args:
            var_name (str): The name of the variable to mark.

        Raises:
            RuntimeError: If the variable is not in the memory model.
        """
        if var_name not in self.variables:
            raise RuntimeError(f'Variable "{var_name}" is not in memory model.')
        self.meta_keygen_seed_vars.push(var_name, None)

    @property
    def meta_keygen_seed_vars(self) -> QueueDict:
        """
        Gets the variable names that have been marked as keygen seed variables.

        Clients should not change these values. Use add_meta_keygen_seed_var() to add
        new keygen seeds metadata.

        Returns:
            QueueDict: The set of keygen seed variable names.
        """
        return self.__meta_keygen_seed_vars

    @property
    def keygen_variables(self) -> dict:
        """
        Gets the set of variable names that have been marked as key material variables.

        Clients should not modify this list. Use add_keygen_variable() to mark a variable
        as key material.

        Returns:
            dict: A dictionary mapping variable names to their generation ordering.
        """
        return self.__keygen_vars

    def add_keygen_variable(self, var_name: str, seed_index: int, key_index: int):
        """
        Marks an existing variable as a key material variable.

        Args:
            var_name (str): The name of the variable to mark.
            seed_index (int): The index of the keygen seed.
            key_index (int): The index of the key.

        Raises:
            RuntimeError: If the variable is not used by the associated kernel, is already marked as key material,
                          or is marked as output.
            IndexError: If the key_index is invalid or the seed_index is out of range.
        """
        if var_name not in self.variables:
            raise RuntimeError(f'Variable "{var_name}" is not used by associated kernel.')
        if var_name in self.keygen_variables:
            raise RuntimeError(f'Variable "{var_name}" is marked already as key material.')
        if var_name in self.output_variables:
            raise RuntimeError(f'Variable "{var_name}" is marked as output and cannot be marked as key material.')
        if key_index < 0:
            raise IndexError('`key_index` must be a valid zero-based index.')
        if seed_index < 0 or seed_index >= len(self.meta_keygen_seed_vars):
            raise IndexError(('`seed_index` must be a valid index into the existing keygen seeds. '
                              'Expected value in range [0, {}), but {} received.').format(len(self.meta_keygen_seed_vars),
                                                                                          seed_index))

        self.keygen_variables[var_name] = (seed_index, key_index)

    def isVarInMem(self, var_name: str) -> bool:
        """
        Checks whether the specified variable is in memory.

        Args:
            var_name (str): The name of the variable to check.

        Returns:
            bool: True if the variable is loaded into the register file, SPAD, or HBM. False otherwise.

        Raises:
            ValueError: If the variable is not in the memory model.
        """

        if var_name not in self.variables:
            raise ValueError(f'`var_name`: "{var_name}" not in memory model.')

        variable: Variable = self.variables[var_name]
        return variable.hbm_address >= 0 or variable.spad_address >= 0 or variable.register is not None

    def retrieveVarAdd(self,
                       var_name: str,
                       suggested_bank: int = -1) -> Variable:
        """
        Retrieves a Variable object from the global list of variables or add a new variable if not found.

        Args:
            var_name (str): The name of the variable to retrieve or add.
            suggested_bank (int, optional): The suggested bank for the variable. Defaults to -1.

        Returns:
            Variable: The Variable object with the given name.

        Raises:
            ValueError: If the suggested bank does not match the existing variable's suggested bank.
        """

        retval = self.variables[var_name] if var_name in self.variables else None
        if not retval:
            retval = Variable(var_name, suggested_bank)
            self.variables[retval.name] = retval
        if retval.suggested_bank < 0:
            retval.suggested_bank = suggested_bank
        elif suggested_bank >= 0:
            if retval.suggested_bank != suggested_bank:
                raise ValueError(('`suggested_bank`: value {} does not match existing variable "{}" '
                                  'suggested bank of {}.').format(suggested_bank,
                                                                  var_name,
                                                                  retval.suggested_bank))
        return retval

    def findUniqueVarName(self) -> str:
        """
        Find a unique variable name that is not already in use.

        Returns:
            str: A unique variable name.
        """
        retval = "_0"
        idx = 1
        while retval in self.variables:
            retval = f"_{idx}"
            idx += 1
        return retval

    def __dumpVariables(self, ostream):
        """
        Dump the variables to the specified output stream.

        Args:
            ostream: The output stream to write the variable information to.
        """
        print("name, hbm, spad, spad dirty, suggested bank, register, register_dirty, last xinst use, pending xinst use", file=ostream)
        for _, variable in self.variables.items():
            print('{}, {}, {}, {}, {}, {}, {}'.format(variable.name,
                                                      variable.hbm_address,
                                                      variable.spad_address,
                                                      variable.spad_dirty,
                                                      variable.suggested_bank,
                                                      variable.register,
                                                      variable.register_dirty,
                                                      repr(variable.last_x_access),
                                                      repr(variable.accessed_by_xinsts)),
                  file = ostream)

    def dump(self,
             output_dir = ''):
        """
        Dump the memory model information to files in the specified output directory.

        Args:
            output_dir (str, optional): 
                The directory to write the dump files to. 
                Defaults to the current working directory.
        """
        if not output_dir:
            output_dir = os.path.join(pathlib.Path.cwd(), "tmp")
        pathlib.Path(output_dir).mkdir(exist_ok = True, parents=True)
        print('******************')
        print(f'Dumping to: {output_dir}')

        vars_filename = os.path.join(output_dir, "variables.dump.csv")
        hbm_filename = os.path.join(output_dir, "hbm.dump.csv")
        spad_filename = os.path.join(output_dir, "spad.dump.csv")

        with open(vars_filename, 'w') as outnum:
            self.__dumpVariables(outnum)
        with open(hbm_filename, 'w') as outnum:
            self.hbm.dump(outnum)
        with open(spad_filename, 'w') as outnum:
            self.spad.dump(outnum)
        for idx, rb in enumerate(self.register_banks):
            register_filename = os.path.join(output_dir, f"register_bank_{idx}.dump.csv")
            with open(register_filename, 'w') as outnum:
                rb.dump(outnum)

        print('******************')
