from linker.instructions import minst
from linker.instructions import cinst
from linker.instructions import xinst
from linker.instructions import dinst
from linker import instructions
from assembler.memory_model.mem_info import MemInfo

def load_minst_kernel(line_iter) -> list:
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
        minstr = instructions.create_from_str_line(s_line, minst.factory())
        if not minstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(minstr)
    return retval

def load_minst_kernel_from_file(filename: str) -> list:
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
            return load_minst_kernel(kernel_minsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e

def load_cinst_kernel(line_iter) -> list:
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
        cinstr = instructions.create_from_str_line(s_line, cinst.factory())
        if not cinstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(cinstr)
    return retval

def load_cinst_kernel_from_file(filename: str) -> list:
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
            return load_cinst_kernel(kernel_cinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e

def load_xinst_kernel(line_iter) -> list:
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
        xinstr = instructions.create_from_str_line(s_line, xinst.factory())
        if not xinstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(xinstr)
    return retval

def load_xinst_kernel_from_file(filename: str) -> list:
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
            return load_xinst_kernel(kernel_xinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e

def load_dinst_kernel(line_iter) -> list:
    """
    Loads DInstruction kernel from an iterator of lines.

    Parameters:
        line_iter: An iterator over lines of DInstruction strings.

    Returns:
        list: A list of DInstruction objects.

    Raises:
        RuntimeError: If a line cannot be parsed into an DInstruction.
    """
    retval = []
    for idx, s_line in enumerate(line_iter):
        dinstr = dinst.create_from_mem_line(s_line)
        if not dinstr:
            raise RuntimeError(f'Error parsing line {idx + 1}: {s_line}')
        retval.append(dinstr)
        
    return retval

def load_dinst_kernel_from_file(filename: str) -> list:
    """
    Loads DInstruction kernel from a file.

    Parameters:
        filename (str): The file containing DInstruction strings.

    Returns:
        list: A list of DInstruction objects.

    Raises:
        RuntimeError: If an error occurs while loading the file.
    """
    with open(filename, 'r') as kernel_dinsts:
        try:
            return load_dinst_kernel(kernel_dinsts)
        except Exception as e:
            raise RuntimeError(f'Error occurred loading file "{filename}"') from e
        