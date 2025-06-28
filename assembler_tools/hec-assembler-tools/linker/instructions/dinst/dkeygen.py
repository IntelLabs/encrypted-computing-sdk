from .dinstruction import DInstruction
from assembler.common.config import GlobalConfig
from assembler.memory_model.mem_info import MemInfo

class Instruction(DInstruction):
    """
    Encapsulates a `dkeygen` DInstruction.
    """

    @classmethod
    def _get_num_tokens(cls) -> int:
        """
        Gets the number of tokens allowed for the instruction.

        Returns:
            int: The number of tokens, which is 4.
        """
        return 4

    @classmethod
    def _get_name(cls) -> str:
        """
        Gets the name of the instruction.

        Returns:
            str: The name of the instruction.
        """
        return MemInfo.Const.Keyword.KEYGEN

