
from assembler.common import constants
from assembler.common.cycle_tracking import CycleTracker
from .variable import Variable
from . import mem_utilities as utilities

class RegisterBank:
    """
    Encapsulates a register bank.

    This class provides an iterable over the registers contained in the register bank and
    offers methods to retrieve and manage registers.

    Properties:
        bank_index (int): Index for the bank as specified during construction.
        register_count (int): Number of registers contained in the bank.

    Methods:
        getRegister(idx: int) -> Register:
            Retrieves the register associated with the specified index.

        findAvailableRegister(live_var_names, replacement_policy: str) -> Register:
            Retrieves the next available register or proposes a register to use if all are
            occupied, based on a replacement policy.
    """

    class __RBIterator:
        """
        Allows iteration over the registers in a register bank.
        """
        def __init__(self, obj):
            assert obj is not None and obj.register_count > 0
            self.__obj = obj
            self.__i = 0

        def __next__(self):
            if self.__i >= self.__obj.register_count:
                raise StopIteration()
            retval = self.__obj.getRegister(self.__i)
            self.__i += 1
            return retval

    # Constructor
    # -----------

    def __init__(self,
                 bank_index: int,
                 register_range: range = None):
        """
        Constructs a new RegisterBank object.

        Args:
            bank_index (int): Zero-based index for the bank to create. The memory model typically has 4 banks,
                but this is flexible to create more banks if needed.
            register_range (range, optional): A range for the indices of the registers contained in this register bank.
                Defaults to `range(constants.MemoryModel.NUM_REGISTER_PER_BANKS)`.

        Raises:
            ValueError: If the bank index is negative or if the register range is invalid.
        """
        if bank_index < 0:
            raise ValueError((f'`bank_index`: expected non-negative a index for bank, '
                              f'but {bank_index} received.'))
        if not register_range:
            register_range = range(constants.MemoryModel.NUM_REGISTER_PER_BANKS)
        elif len(register_range) < 1:
            raise ValueError((f'`register_range`: expected a range within [0, {constants.MemoryModel.NUM_REGISTER_PER_BANKS}) with, '
                              f'at least, 1 element, but {register_range} received.'))
        elif abs(register_range.step) != 1:
            raise ValueError((f'`register_range`: expected a range within step of 1 or -1, '
                              f'but {register_range} received.'))
        self.__bank_index = bank_index
        # list of registers in this bank
        self.__registers = [ Register(self, register_i) for register_i in register_range ]

    # Special methods
    # ---------------

    def __iter__(self):
        """
        Returns an iterator over the registers in the register bank.

        Returns:
            __RBIterator: An iterator over the registers.
        """
        return RegisterBank.__RBIterator(self)

    def __repr__(self):
        """
        Returns a string representation of the RegisterBank object.

        Returns:
            str: A string representation of the RegisterBank.
        """
        return '<{}  object at {}>(bank_index = {})'.format(type(self).__name__,
                                                            hex(id(self)),
                                                            self.bank_index)

    # Methods and properties
    # ----------------------

    @property
    def bank_index(self) -> int:
        """
        Gets the index of the bank.

        Returns:
            int: The index of the bank.
        """
        return self.__bank_index

    @property
    def register_count(self) -> int:
        """
        Gets the number of registers in this bank.

        Returns:
            int: The number of registers.
        """
        return len(self.__registers)

    def getRegister(self, idx: int):
        """
        Retrieves the register associated with the specified index.

        Args:
            idx (int): Index for the register to retrieve. This can be a negative value.

        Returns:
            Register: The register associated with the specified index.

        Raises:
            ValueError: If the index is out of range.
        """
        if idx < -self.register_count or idx >= self.register_count:
            raise ValueError((f'`idx`: expected an index for register in the range [-{self.register_count}, {self.register_count}), '
                              f'but {idx} received.'))
        return self.__registers[idx]

    def findAvailableRegister(self,
                              live_var_names,
                              replacement_policy: str = None):
        """
        Retrieve the next available register or propose a register to use if all are occupied.

        Args:
            live_var_names (set or list): 
                A set of variable names containing the variables that are not available for replacement
                i.e. live variables. This is used to avoid replacing variables that were just allocated
                as dependencies for an upcoming instruction.

            replacement_policy (str, optional):
                If specified, it must be a value from `Constants.REPLACEMENT_POLICIES`. Otherwise,
                this method will not find a location to replace if all registers are occupied.
                Values:
                - `Constants.REPLACEMENT_POLICY_FTBU`: suggests replacement of variable that is furthest accessed
                    (using LRU and number of usages left as tie breakers).
                - `Constants.REPLACEMENT_POLICY_LRU`: suggests replacement of the least recently accessed variable.

        Returns:
            Register: The first empty register, or the register to replace if all are occupied. Returns None if no suitable register is found.
        """
        retval_idx = utilities.findAvailableLocation((register.contained_variable for register in self.__registers),
                                                     live_var_names,
                                                     replacement_policy)
        return self.getRegister(retval_idx) if retval_idx >= 0 else None

    def dump(self, ostream):
        """
        Dump the current state of the register bank to the specified output stream.

        Args:
            ostream: The output stream to write the register bank state to.
        """
        print(f'Register bank, {self.bank_index}', file = ostream)
        print(f'Number of registers, {self.register_count}', file = ostream)
        print("", file = ostream)
        print("register, variable, variable register, dirty", file = ostream)
        for idx in range(self.register_count):
            register = self.getRegister(idx)
            if not register:
                print('ERROR: None Register')
            else:
                var_data = 'None'
                variable = register.contained_variable
                if variable is not None:
                    if variable.name:
                        var_data = '{}, {}'.format(variable.name,
                                                   variable.register,
                                                   variable.register_dirty)
                    else:
                        var_data = f'Dummy_{variable.tag}'
                print('{}, {}'.format(register.name,
                                      var_data),
                      file = ostream)

class Register(CycleTracker):
    """
    Represents a register in the register file.

    Inherits from CycleTracker to manage the cycle when the register is ready to be used.
    This class tracks the register name, the variable contained within the register as a form
    of inverse look-up, and whether the register contents are "dirty".

    A register is identified by its bank and index inside the bank. The name of the
    register is formatted as `r<register>b<bank>`. For example, register 5 in bank 1 has the name `r5b1`.

    Properties:
        bank (RegisterBank): The bank where this register resides.
        name (str): The name of this register, built from the bank and register indices.
        register_index (int): The index for this register inside its bank.
        register_dirty (bool): Specifies whether the register is "dirty". A register is dirty if it has
            been written to but has not been saved into SPAD.
        contained_variable (Variable): The variable contained in this register, or None if no variable is currently
            contained in this register. This is used as a form of inverse look-up.
    """

    # Constructor
    # -----------

    def __init__(self,
                 bank: RegisterBank,
                 register_index: int):
        """
        Initializes a new Register object.

        Args:
            bank (RegisterBank): The bank to which this register belongs.
            register_index (int): The index of the register inside the bank.

        Raises:
            ValueError: If the register index is out of the valid range.
        """
        if register_index < 0 or register_index >= constants.MemoryModel.NUM_REGISTER_PER_BANKS:
            raise ValueError((f'`register_index`: expected an index for register in the range [0, {constants.MemoryModel.NUM_REGISTER_PER_BANKS}), '
                              f'but {register_index} received.'))
        super().__init__((0, 0))
        self.register_dirty = False
        self.__bank = bank
        self.__register_index = register_index
        self.__contained_var = None

    # Special methods
    # ---------------

    def __eq__(self, other):
        """
        Checks equality with another Register object.

        Args:
            other (Register): The other Register to compare with.

        Returns:
            bool: True if the other Register is the same as this one, False otherwise.
        """
        return other is self \
            or (isinstance(other, Register) and other.name == self.name)

    def __hash__(self):
        """
        Returns the hash of the register's name.

        Returns:
            int: The hash of the register's name.
        """
        return hash(self.name)

    def __str__(self):
        """
        Returns the name of the register as its string representation.

        Returns:
            str: The name of the register.
        """
        return self.name

    def __repr__(self):
        """
        Returns a string representation of the Register object.

        Returns:
            str: A string representation of the Register.
        """
        var_section = ""
        if self.contained_variable:
            var_section = "Variable='{}'".format(self.contained_variable.name)
        return '<{}({}) object at {}>({})'.format(type(self).__name__,
                                                  self.name,
                                                  hex(id(self)),
                                                  var_section)

    # Methods and properties
    # ----------------------

    @property
    def name(self) -> str:
        """
        Gets the name of the register.

        Returns:
            str: The name of the register.
        """
        return f"r{self.register_index}b{self.bank.bank_index}"

    @property
    def bank(self) -> RegisterBank:
        """
        Gets the bank where this register resides.

        Returns:
            RegisterBank: The bank of the register.
        """
        return self.__bank

    @property
    def register_index(self) -> int:
        """
        Gets the index of the register inside its bank.

        Returns:
            int: The index of the register.
        """
        return self.__register_index

    @property
    def contained_variable(self) -> Variable:
        """
        Gets or sets the variable contained in this register.

        Returns:
            Variable: The variable contained in this register, or None if no variable is contained.
        """
        return self.__contained_var

    def _set_contained_variable(self, value):
        """
        Sets the variable contained in this register.

        Args:
            value (Variable): The variable to set, or None to clear the register.

        Raises:
            ValueError: If the value is not a Variable.
        """
        if value:
            if not isinstance(value, Variable):
                raise ValueError('`value`: expected a `Variable`.')
        self.__contained_var = value
        # register no longer dirty because we are overwriting it with new variable (or None to clear)
        self.register_dirty = False

    def allocateVariable(self, variable: Variable = None):
        """
        Allocates the specified variable into this register, or frees this register if
        the specified variable is None.

        The register and the newly allocated variable are no longer dirty after this allocation.

        Args:
            variable (Variable, optional): The variable to allocate, or None to free the register.
        """
        old_var: Variable = self.contained_variable
        if old_var:
            # make old variable aware that it is no longer in this register
            assert(not old_var.register_dirty) # we should not be deallocating dirty variables
            old_var.register = None
        if variable:
            # make variable aware of new register
            old_reg = variable.register
            if old_reg:
                # free old register, if any
                old_reg._set_contained_variable(None)
            variable.register = self

        self._set_contained_variable(variable)

    def toCASMISAFormat(self) -> str:
        """
        Converts the register to CInst ASM-ISA format.

        Returns:
            str: The CInst ASM-ISA format of the register.
        """
        return self.name

    def toXASMISAFormat(self) -> str:
        """
        Converts the register to XInst ASM-ISA format.

        Returns:
            str: The XInst ASM-ISA format of the register.
        """
        return self.name
