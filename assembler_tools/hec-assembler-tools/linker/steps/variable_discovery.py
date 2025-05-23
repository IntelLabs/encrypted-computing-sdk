from assembler.memory_model.variable import Variable
from linker.instructions import minst, cinst
from linker.instructions.minst.minstruction import MInstruction
from linker.instructions.cinst.cinstruction import CInstruction

def discoverVariablesSPAD(cinstrs: list):
    """
    Finds Variable names used in a list of CInstructions.
    
    Attributes:
        cinstrs (list[CInstruction]):
            List of CInstructions where to find variable names.
    Raises:
        RuntimeError:
            Invalid Variable name detected in an CInstruction.
    Returns:
        Iterable:
            Yields an iterable over variable names identified in the listing
            of CInstructions specified.
    """
    for idx, cinstr in enumerate(cinstrs):
        if not isinstance(cinstr, CInstruction):
            raise TypeError(f'Item {idx} in list of MInstructions is not a valid MInstruction.')
        retval = None
        # TODO: Implement variable counting for CInst
        ###############
        # Raise NotImplementedError("Implement variable counting for CInst")
        if isinstance(cinstr, (cinst.BLoad, cinst.CLoad, cinst.BOnes, cinst.NLoad)):
            retval = cinstr.source
        elif isinstance(cinstr, cinst.CStore):
            retval = cinstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(f'Invalid Variable name "{retval}" detected in instruction "{idx}, {cinstr.to_line()}"')
            yield retval

def discoverVariables(minstrs: list):
    """
    Finds variable names used in a list of MInstructions.

    Parameters:
        minstrs (list[MInstruction]): List of MInstructions where to find variable names.

    Raises:
        TypeError: If an item in the list is not a valid MInstruction.
        RuntimeError: If an invalid variable name is detected in an MInstruction.

    Returns:
        Iterable: Yields an iterable over variable names identified in the listing
                  of MInstructions specified.
    """
    for idx, minstr in enumerate(minstrs):
        if not isinstance(minstr, MInstruction):
            raise TypeError(f'Item {idx} in list of MInstructions is not a valid MInstruction.')
        retval = None
        if isinstance(minstr, minst.MLoad):
            retval = minstr.source
        elif isinstance(minstr, minst.MStore):
            retval = minstr.dest

        if retval is not None:
            if not Variable.validateName(retval):
                raise RuntimeError(f'Invalid Variable name "{retval}" detected in instruction "{idx}, {minstr.to_line()}"')
            yield retval