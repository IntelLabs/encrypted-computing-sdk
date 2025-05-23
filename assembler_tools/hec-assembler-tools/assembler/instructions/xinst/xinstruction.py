from argparse import Namespace

from assembler.common import constants
from assembler.common.cycle_tracking import CycleType
from assembler.common.decorators import *
from assembler.memory_model.variable import Variable
from assembler.memory_model.register_file import Register
from ..instruction import BaseInstruction
from .. import tokenizeFromLine

class XInstruction(BaseInstruction):
    """
    This class is used to encapsulate the properties and behaviors of an xinstruction,
    including its throughput, latency, and optional residual.

    Static Methods:
        tokenizeFromPISALine: Checks if the specified instruction can be parsed from the specified line and returns the tokenized line.
        parsePISASourceDestsFromTokens: Parses the sources and destinations for an instruction from tokens in P-ISA format.
        reset_GlobalCycleReady: Resets global cycle tracking for derived classes.

    Methods:
        N: Returns the ring size for the operation.
        res: Returns the residual for the operation.
    """

    @staticmethod
    def tokenizeFromPISALine(op_name: str, line: str) -> list:
        """
        Checks whether the specified instruction can be parsed from the specified
        line and, if so, returns the tokenized line.

        Parameters:
            op_name (str): Name of operation that should be contained in the line.

            line (str): Line to tokenize.

        Returns:
            tuple: A tuple containing tokens (tuple of str) and comment (str), or None if the instruction cannot be parsed from the line.
        """
        retval = None
        tokens, comment = tokenizeFromLine(line)
        if len(tokens) > 1 and tokens[1] == op_name:
            retval = (tokens, comment)
        return retval

    @staticmethod
    def parsePISASourceDestsFromTokens(tokens: list,
                                       num_dests: int,
                                       num_sources: int,
                                       offset: int = 0) -> dict:
        """
        Parses the sources and destinations for an instruction, given sources and
        destinations in tokens in P-ISA format.

        Parameters:
            tokens (list of str): List of string tokens where each token corresponds to a destination or
                                  a source for the instruction being parsed, in order.

            num_dests (int): Number of destinations for the instruction.

            num_sources (int): Number of sources for the instruction.

            offset (int, optional): Offset in the list of tokens where to start parsing. Defaults to 0.

        Returns:
            dict: A dictionary with, at most, two keys: "src" and "dst", representing the parsed sources
                  and destinations for the instruction. The value for each key is a list of parsed
                  `Variable` tuples.
        """
        retval = {}
        dst_start = offset
        dst_end = dst_start + num_dests
        dst = []
        for dst_token in tokens[dst_start:dst_end]:
            dst.append(Variable.parseFromPISAFormat(dst_token))
        src_start = dst_end
        src_end = src_start + num_sources
        src = []
        for src_token in tokens[src_start:src_end]:
            src.append(Variable.parseFromPISAFormat(src_token))
        if dst:
            retval["dst"] = dst
        if src:
            retval["src"] = src
        return retval

    @classmethod
    def reset_GlobalCycleReady(cls, value=CycleType(0, 0)):
        """
        If derived classes have global cycle tracking, they should override this
        method to reset their global cycle tracking when called.

        Parameters:
            value (CycleType, optional): The cycle type value to reset to. Defaults to CycleType(0, 0).
        """
        pass

    def __init__(self,
                 id: int,
                 N: int,
                 throughput: int,
                 latency: int,
                 res: int = None,
                 comment: str = ""):
        """
        Constructs a new XInstruction.

        Parameters:
            id (int): User-defined ID for the instruction. It will be bundled with a nonce to form a unique ID.

            N (int): Ring size for the operation, Log2(PMD). Set to `0` if not known.

            throughput (int): The throughput of the instruction.

            latency (int): The latency of the instruction.

            res (int, optional): The residual for the operation. Defaults to None.

            comment (str, optional): A comment for the instruction. Defaults to an empty string.
        """
        if res is not None and res >= constants.MemoryModel.MAX_RESIDUALS:
            comment = f"res = {res}" + ("; " + comment if comment else "")
        super().__init__(id, throughput, latency, comment=comment)
        self.__n = N # Read-only ring size for the operation
        self.__res = res # Read-only residual

    @property
    def N(self) -> int:
        """
        Ring size, Log2(PMD). This is just for tracking purposes. Set to `0` if not known.

        Returns:
            int: The ring size for the operation.
        """
        return self.__n

    @property
    def res(self) -> int:
        """
        Residual for the operation, or None if operation does not support residuals.

        Returns:
            int: The residual for the operation.
        """
        return self.__res

    def _schedule(self, cycle_count: CycleType, schedule_id: int) -> int:
        """
        Schedules the instruction, simulating timings of executing this instruction.

        The ready cycle for all destinations is updated based on input `cycle_count` and
        this instruction latency.

        All variables in the instruction sources and destinations are updated to reflect
        the variable access.

        Derived classes can override to add their own simulation rules.

        Parameters:
            cycle_count (CycleType): Current cycle of execution.

            schedule_id (int): 1-based index for this instruction in its schedule listing.

        Raises:
            RuntimeError: The instruction is not ready to execute yet. Based on current cycle,
                          the instruction is ready to execute if its cycle_ready value is less than or
                          equal to `cycle_count`.

        Returns:
            int: The throughput for this instruction. i.e. the number of cycles by which to advance
                 the current cycle counter.
        """
        retval = super()._schedule(cycle_count, schedule_id)

        # Update accessed cycle and access instruction of variables
        vars = set(v for v in self.sources + self.dests if isinstance(v, Variable))
        for v in vars:
            # Check that variable is in register file
            if not v.register:
                # All variables must be in register before scheduling instruction
                raise RuntimeError('Instruction( {}, id={} ): Variable {} not in register file.'.format(self.name,
                                                                                                        self.id,
                                                                                                        v.name))
            # Update accessed cycle
            v.last_x_access = cycle_count
            # Remove this instruction from access list
            accessed_idx = -1
            for idx, access_element in enumerate(v.accessed_by_xinsts):
                if access_element.instruction_id == self.id:
                    accessed_idx = idx
                    break
            assert(accessed_idx >= 0)
            v.accessed_by_xinsts = v.accessed_by_xinsts[:accessed_idx] + v.accessed_by_xinsts[accessed_idx + 1:]

        # Update ready cycle and dirty state of dests
        for dst in self.dests:
            dst.cycle_ready = CycleType(cycle_count.bundle, cycle_count.cycle + self.latency)
            dst.register_dirty = True

        return retval

    def _toPISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to P-ISA kernel format.

        See inherited for more information.

        Parameters:
            extra_args: Additional arguments for formatting.

        Returns:
            str: The instruction in P-ISA kernel format.
        """
        preamble = (self.N,)
        extra_args = tuple(src.toPISAFormat() for src in self.sources) + extra_args
        extra_args = tuple(dst.toPISAFormat() for dst in self.dests) + extra_args
        if self.res is not None:
            extra_args += (self.res,)
        return self.toStringFormat(preamble,
                                   self.OP_NAME_PISA,
                                   *extra_args)

    def _toXASMISAFormat(self, *extra_args) -> str:
        """
        Converts the instruction to ASM-ISA format.

        See inherited for more information.

        Parameters:
            extra_args: Additional arguments for formatting.

        Returns:
            str: The instruction in ASM-ISA format.
        """
        # preamble = (self.id[0], self.N)
        preamble = (self.id[0],)
        # Instruction sources
        extra_args = tuple(src.toXASMISAFormat() for src in self.sources) + extra_args
        # Instruction destinations
        extra_args = tuple(dst.toXASMISAFormat() for dst in self.dests) + extra_args
        if self.res is not None:
            extra_args += (self.res % constants.MemoryModel.MAX_RESIDUALS,)
        return self.toStringFormat(preamble,
                                   self.OP_NAME_ASM,
                                   *extra_args)
    
    @classmethod
    def _get_OP_NAME_ASM(cls) -> str:
        """
        Returns the operation name in ASM format.

        Returns:
            str: ASM format operation.
        """
        return "default_op"  # Provide a default operation name or a meaningful one if applicable