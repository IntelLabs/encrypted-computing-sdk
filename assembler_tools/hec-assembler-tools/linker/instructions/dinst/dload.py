from .dinstruction import DInstruction
from assembler.memory_model.mem_info import MemInfo

class Instruction(DInstruction):
    """
    Encapsulates a `dload` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> tuple:
        """
        Gets the number of tokens allowed for the instruction.

        Returns:
            tupple: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction.
        """
        return MemInfo.Const.Keyword.LOAD
    
    @property
    def tokens(self) -> list:
        """
        Gets the list of tokens for the instruction.

        Returns:
            list: The list of tokens.
        """
        return [self.name, self._tokens[1], str(self.address)] + self._tokens[3:]
    
