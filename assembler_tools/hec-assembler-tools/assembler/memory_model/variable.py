import re
from typing import NamedTuple

from assembler.common import constants
from assembler.common.config import GlobalConfig
from assembler.common.cycle_tracking import CycleTracker, CycleType

class Variable(CycleTracker):
    """
    Class to represent a variable within a memory model.

    Inherits from CycleTracker to manage the cycle when the variable is ready to be used.
    This class tracks the variable's name, its location across the memory model, and its readiness cycle.

    Attributes:
        hbm_address (int):
            HBM data region address (zero-based word index) where this variable is stored.
            Set to -1 if not stored.
        accessed_by_xinsts (list[AccessElement]):
            List of XInstruction IDs that will access this variable.
            The elements of the list also contain an ordering index estimating the index of the instruction
            in the instructions listing.
        last_x_access (XInstruction):
            Last XInstruction that accessed this variable (either read or write).

    Properties:
        name (str):
            Name of the variable.
        suggested_bank (int):
            The suggested bank for the variable in the range [0, NUM_REGISTER_BANKS)
            or a negative number if no bank is suggested. Setting it to a negative number is ignored.
        register (Register):
            Specifies the register for this variable. `None` if not allocated in a register.
        register_dirty (bool):
            Specifies whether the register for this variable is "dirty".
        spad_address (int):
            Specifies the SPAD address for this variable. -1 if not stored in SPAD.
        spad_dirty (bool):
            Specifies whether the SPAD location for this variable is "dirty".
    """

    class AccessElement(NamedTuple):
        """
        Structured tuple to contain an instruction ID and its index in the ordered instruction listing.

        Attributes:
            index (int): The index of the instruction in the listing.
            instruction_id (tuple): The ID of the instruction.
        """
        index: int
        instruction_id: tuple

    # Static methods
    # --------------

    @classmethod
    def parseFromPISAFormat(cls, s_pisa: str):
        """
        Parses a `Variable` from P-ISA format and return a tuple that can be used to construct a `Variable` object.

        Args:
            s_pisa (str): String containing the P-ISA variable format. It has the form:
                `<var_name> (<suggested_reg>)` where <suggested_reg> is optional (parentheses are ignored).

        Raises:
            ValueError: If the input is in an invalid P-ISA format.

        Returns:
            tuple: A tuple representing the parsed information that can be used to construct a `Variable` object.
        """
        tokens = list(map(lambda s: s.strip(), s_pisa.split()))
        if len(tokens) > 2 or len(tokens) < 1:
            raise ValueError(f'Invalid format for P-ISA variable: {s_pisa}.')
        if len(tokens) < 2:
            # default to suggested bank -1
            tokens.append(-1)
        else:
            tokens[1] = int(tokens[1].strip("()"))
        return tuple(tokens)

    @classmethod
    def validateName(cls, name: str) -> bool:
        """
        Validates whether a name is an appropriate identifier for a variable.

        Args:
            name (str): Variable name to validate.

        Returns:
            bool: True if the name is a valid variable identifier, False otherwise.
        """
        retval = True
        if name:
            name = name.strip()
        if not name:
            retval = False
        if retval and not re.search('^[A-Za-z_][A-Za-z0-9_]*', name):
            retval = False
        return retval


    # Constructor
    # -----------

    def __init__(self,
                 var_name: str,
                 suggested_bank: int = -1):
        """
        Constructs a new Variable object with a specified name and suggested bank number.

        Args:
            var_name (str): Name of the variable. Must be an identifier.
            suggested_bank (int, optional): Suggested bank for the variable in the range [0, NUM_REGISTER_BANKS)
                or a negative number if no bank is suggested. Defaults to -1.

        Raises:
            ValueError: If the variable name is invalid or the suggested bank is out of range.
        """

        # validate the variable name to be an identifier
        if not self.validateName(var_name):
            raise ValueError((f'`var_name`: Invalid variable name "{var_name}".'))
        self.__var_name = var_name.strip()
        # validate bank number
        if suggested_bank >= constants.MemoryModel.NUM_REGISTER_BANKS:
            raise ValueError(("`suggested_bank`: Expected negative to indicate no "
                             "suggestion or a bank index less than {}, but {} received.").format(
                                 constants.MemoryModel.NUM_REGISTER_BANKS, suggested_bank))

        super().__init__(CycleType(0, 0)) # cycle ready in the form (bundle, clock_cycle)

        self.__suggested_bank = suggested_bank
        # HBM data region address (zero-based word index) where this variable is stored.
        # Set to -1 if not stored.
        self.hbm_address = -1
        self.__spad_address = -1
        self.__spad_dirty = False
        self.__register = None # Register
        self.__register_dirty = False
        self.accessed_by_xinsts = [] # list of AccessElements containing instruction IDs that access this variable
        self.last_x_access = None # last xinstruction that accessed this variable

    # Special methods
    # ---------------

    def __repr__(self):
        """
        Returns a string representation of the Variable object.

        Returns:
            str: A string representation.
        """
        retval = '<{} object at {}>(var_name="{}", suggested_bank={})'.format(type(self).__name__,
                                                                              hex(id(self)),
                                                                              self.name,
                                                                              self.suggested_bank)
        return retval

    def __str__(self):
        """
        Returns the name of the variable as its string representation.

        Returns:
            str: The name of the variable.
        """
        return self.name

    def __eq__(self, other):
        """
        Checks equality with another Variable object.

        Args:
            other (Variable): The other Variable to compare with.

        Returns:
            bool: True if the other Variable is the same as this one, False otherwise.
        """
        return other is self

    def __hash__(self):
        """
        Returns the hash of the variable's name.

        Returns:
            int: The hash.
        """
        return hash(self.name)

    # Methods and properties
    # ----------------------

    def _get_var_name(self):
        """
        Gets the name of the variable.

        Returns:
            str: The name of the variable.
        """
        return self.__var_name

    @property
    def name(self):
        """
        Gets the name of the variable.

        Returns:
            str: The name of the variable.
        """
        return self._get_var_name()

    @property
    def suggested_bank(self):
        """
        Gets or sets the suggested bank for the variable.

        Returns:
            int: The suggested bank for the variable.
        """
        return self.__suggested_bank

    @suggested_bank.setter
    def suggested_bank(self, value: int):
        if value >= constants.MemoryModel.NUM_REGISTER_BANKS:
            raise ValueError('`value`: must be in range [0, {}), but {} received.'.format(constants.MemoryModel.NUM_REGISTER_BANKS,
                                                                                          str(value)))
        if value >= 0: # ignore negative values
            self.__suggested_bank = value

    @property
    def register(self):
        """
        Gets or sets the register for this variable.

        Returns:
            Register: The register for this variable, or `None` if not allocated in a register.
        """
        return self.__register

    @register.setter
    def register(self, value):
        self._set_register(value)

    def _set_register(self, value):
        from .register_file import Register
        if value:
            if not isinstance(value, Register):
                raise ValueError(('`value`: expected a `Register`, but received a `{}`.'.format(type(value).__name__)))
            self.__register = value
        else:
            self.__register = None
            self.register_dirty = False
        self.last_x_access = None # new Register, so, no XInst access yet

    @property
    def register_dirty(self) -> bool:
        """
        Gets or sets whether the register for this variable is "dirty".

        Returns:
            bool: True if the register is dirty, False otherwise.
        """
        return self.register.register_dirty if self.register else False

    @register_dirty.setter
    def register_dirty(self, value: bool):
        if self.register:
            self.register.register_dirty = value

    @property
    def spad_address(self) -> int:
        """
        Gets or sets the SPAD address for this variable.

        Returns:
            int: The SPAD address, or -1 if not stored in SPAD.
        """
        return self.__spad_address

    @spad_address.setter
    def spad_address(self, value: int):
        self._set_spad_address(value)

    def _set_spad_address(self, value: int):
        self.spad_dirty = False # SPAD is no longer dirty because we are overwriting it
        if value < 0:
            self.__spad_address = -1
        else:
            self.__spad_address = value

    @property
    def spad_dirty(self) -> bool:
        """
        Gets or sets whether the SPAD location for this variable is "dirty".

        Returns:
            bool: True if the SPAD location is dirty, False otherwise.
        """
        return self.spad_address >= 0 and self.__spad_dirty

    @spad_dirty.setter
    def spad_dirty(self, value: bool):
        self.__spad_dirty = value

    def _get_cycle_ready(self) -> CycleType:
        """
        Returns the current value for the ready cycle.

        Ready cycle for a variable is the maximum among its internal ready cycle and
        the ready cycle of any of its locations (currently, only registers have a ready cycle).

        Returns:
            CycleType: The current value for the ready cycle.
        """
        retval = super()._get_cycle_ready()
        if self.register and self.register.cycle_ready > retval:
            retval = self.register.cycle_ready

        return retval

    def toPISAFormat(self) -> str:
        """
        Converts the variable to P-ISA kernel format.

        Returns:
            str: The P-ISA format of the variable.
        """
        retval = f'{self.name}'
        if self.suggested_bank >= 0:
            retval += f' ({self.suggested_bank})'
        return retval

    def toXASMISAFormat(self) -> str:
        """
        Converts the variable to XInst ASM-ISA format.

        Returns:
            str: The XInst ASM-ISA format of the variable.

        Raises:
            RuntimeError: If the variable is not allocated to a register.
        """
        if not self.register:
            raise RuntimeError("`Variable` object not allocated to register. Cannot convert to XInst ASM-ISA format.")
        return self.register.toXASMISAFormat()

    def toCASMISAFormat(self) -> str:
        """
        Converts the variable to CInst ASM-ISA format.

        Returns:
            str: The CInst ASM-ISA format of the variable.

        Raises:
            RuntimeError: If the variable is not stored in SPAD.
        """
        if self.spad_address < 0:
            raise RuntimeError("`Variable` object not allocated in SPAD. Cannot convert to CInst ASM-ISA format.")
        return self.spad_address if GlobalConfig.hasHBM else self.name

    def toMASMISAFormat(self) -> str:
        """
        Converts the variable to MInst ASM-ISA format.

        Returns:
            str: The MInst ASM-ISA format of the variable.

        Raises:
            RuntimeError: If the variable is not stored in HBM.
        """
        if self.hbm_address < 0:
            raise RuntimeError("`Variable` object not allocated in HBM. Cannot convert to MInst ASM-ISA format.")
        return self.name if GlobalConfig.useHBMPlaceHolders else self.hbm_address

def findVarByName(vars_lst, var_name: str) -> Variable:
    """
    Finds the first variable in an iterable of Variable objects that matches the specified name.

    Args:
        vars_lst (iterable[Variable]): An iterable collection of Variable objects.
        var_name (str): The name of the variable to find in `vars_lst`.

    Returns:
        Variable: The first Variable object in `vars_lst` with a name matching `var_name`, or None if no match is found.
    """
    return next((var for var in vars_lst if var.name == var_name), None)

class DummyVariable(Variable):
    """
    Represents a dummy variable used as a placeholder.

    A dummy variable serves as a placeholder to indicate registers that will be available in the next bundle,
    but not in the current one, such as after a `move` operation. It can be identified by its empty name.
    """

    # Constructor
    # -----------

    def __init__(self, tag = None):
        """
        Initializes a new DummyVariable object.

        Args:
            tag (optional): An optional tag to associate with the dummy variable. Defaults to 0 if not provided.
        """
        super().__init__("dummy")
        self.tag = 0 if tag is None else tag

    def _get_var_name(self):
        """
        Get the name of the dummy variable.

        Returns:
            str: An empty string, indicating the variable is a dummy.
        """
        return ""

    def _set_register(self, value):
        """
        Overrides the method to set the register for the dummy variable.

        This method does nothing for a dummy variable.
        """
        pass

    def _set_spad_address(self, value: int):
        """
        Overrides the method to set the SPAD address for the dummy variable.

        This method does nothing for a dummy variable.
        """
        pass
