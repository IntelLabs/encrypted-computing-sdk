from .dinstruction import DInstruction
from assembler.common.config import GlobalConfig
from assembler.memory_model.mem_info import MemInfo

class Instruction(DInstruction):
    """
    Encapsulates a `dstore` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens allowed for the instruction.

        Returns:
            int: The number of tokens, which is 3.
        """
        return 3

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction.
        """
        return MemInfo.Const.Keyword.STORE

    @property
    def tokens(self) -> list:
        """
        Gets the list of tokens for the instruction.

        Returns:
            list: The list of tokens.
        """
        return [self.name, self.var, str(self.address)] + self._tokens[3:]
