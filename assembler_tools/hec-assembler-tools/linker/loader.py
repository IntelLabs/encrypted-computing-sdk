from linker.instructions import minst
from linker.instructions import cinst
from linker.instructions import xinst
from linker import instructions

def loadMInstKernel(line_iter) -> list:
    """
    Loads MInstruction kernel from an iterator of lines.

    Parameters:
        line_iter: An iterator over lines of MInstruction strings.

    Returns:
        list: A list of MInstruction objects.

    Raises:
        RuntimeError: If a line cannot be parsed into an MInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        minstr = instructions.fromStrLine(s_line, minst.factory())
        if not minstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(minstr)
    return retval

def loadMInstKernelFromFile(filename: str) -> list:
    """
    Loads MInstruction kernel from a file.

    Parameters:
        filename (str): The file containing MInstruction strings.

    Returns:
        list: A list of MInstruction objects.

    Raises:
        RuntimeError: If an error occurs while loading the file.
    """
    with open(filename, 'r') as kernel_minsts:
        try:
            return loadMInstKernel(kernel_minsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e

def loadCInstKernel(line_iter) -> list:
    """
    Loads CInstruction kernel from an iterator of lines.

    Parameters:
        line_iter: An iterator over lines of CInstruction strings.

    Returns:
        list: A list of CInstruction objects.

    Raises:
        RuntimeError: If a line cannot be parsed into a CInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        cinstr = instructions.fromStrLine(s_line, cinst.factory())
        if not cinstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(cinstr)
    return retval

def loadCInstKernelFromFile(filename: str) -> list:
    """
    Loads CInstruction kernel from a file.

    Parameters:
        filename (str): The file containing CInstruction strings.

    Returns:
        list: A list of CInstruction objects.

    Raises:
        RuntimeError: If an error occurs while loading the file.
    """
    with open(filename, 'r') as kernel_cinsts:
        try:
            return loadCInstKernel(kernel_cinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e

def loadXInstKernel(line_iter) -> list:
    """
    Loads XInstruction kernel from an iterator of lines.

    Parameters:
        line_iter: An iterator over lines of XInstruction strings.

    Returns:
        list: A list of XInstruction objects.

    Raises:
        RuntimeError: If a line cannot be parsed into an XInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        xinstr = instructions.fromStrLine(s_line, xinst.factory())
        if not xinstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(xinstr)
    return retval

def loadXInstKernelFromFile(filename: str) -> list:
    """
    Loads XInstruction kernel from a file.

    Parameters:
        filename (str): The file containing XInstruction strings.

    Returns:
        list: A list of XInstruction objects.

    Raises:
        RuntimeError: If an error occurs while loading the file.
    """
    with open(filename, 'r') as kernel_xinsts:
        try:
            return loadXInstKernel(kernel_xinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e