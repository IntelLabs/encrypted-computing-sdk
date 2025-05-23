from assembler.memory_model import MemoryModel
from .xinstruction import XInstruction
from . import add, sub, mul, muli, mac, maci, ntt, intt, twntt, twintt, rshuffle, irshuffle, move, xstore, nop
from . import exit as exit_mod
from . import copy as copy_mod

# XInst aliases

# XInsts with P-ISA equivalent
Add = add.Instruction
Sub = sub.Instruction
Mul = mul.Instruction
Muli = muli.Instruction
Mac = mac.Instruction
Maci = maci.Instruction
NTT = ntt.Instruction
iNTT = intt.Instruction
twNTT = twntt.Instruction
twiNTT = twintt.Instruction
rShuffle = rshuffle.Instruction
Copy = copy_mod.Instruction
irShuffle = irshuffle.Instruction
# All other XInsts
Move = move.Instruction
XStore = xstore.Instruction
Exit = exit_mod.Instruction
Nop = nop.Instruction

# Collection of XInstructions with P-ISA or intermediate P-ISA equivalents
__PISA_INSTRUCTIONS = ( Add, Sub, Mul, Muli, Mac, Maci, NTT, iNTT, twNTT, twiNTT, rShuffle, irShuffle, Copy )

# Collection of XInstructions with global cycle tracking
GLOBAL_CYCLE_TRACKING_INSTRUCTIONS = ( rShuffle, irShuffle, XStore )

def createFromParsedObj(mem_model: MemoryModel,
                        inst_type,
                        parsed_op,
                        new_id: int = 0) -> XInstruction:
    """
    Creates an XInstruction object XInst from the specified namespace data.

    Variables are extracted from the memory model (or created if not existing) and
    added as destinations and sources to the instruction.

    Parameters:
        mem_model (MemoryModel):
            The MemoryModel object, where all variables are kept. Variables parsed from the
            input string will be automatically added to the memory model if they do not already
            exist. The represented object may be modified if addition is needed.
        inst_type (type):
            Type of the instruction to create. Constructor must be compatible with namespace `parsed_op`.
            This type must be a class derived from `XInstruction`.
        parsed_op (Namespace):
            A namespace that is compatible with the instruction of type `inst_type` to create.
        new_id (int):
            Optional ID number for the instruction. Defaults to 0.

    Returns:
        XInstruction: A XInstruction derived object encapsulating the XInst.

    Raises:
        ValueError: If `inst_type` is not a class derived from `XInstruction`.
    """

    if not issubclass(inst_type, XInstruction):
        raise ValueError('`inst_type`: expected a class derived from `XInstruction`.')

    # Convert variable names into actual variable objects.

    # Find the variables for dst.
    dsts = []
    for var_name, bank in parsed_op.dst:
        # Retrieve variable from global list (or create new one if it doesn't exist).
        var = mem_model.retrieveVarAdd(var_name, bank)
        dsts.append(var)

    # Find the variables for src.
    srcs = []
    for var_name, bank in parsed_op.src:
        # Retrieve variable from global list (or create new one if it doesn't exist).
        var = mem_model.retrieveVarAdd(var_name, bank)
        srcs.append(var)

    # Prepare parsed object to add as arguments to instruction constructor.
    parsed_op.dst = dsts
    parsed_op.src = srcs
    assert(parsed_op.op_name == inst_type.OP_NAME_PISA)
    parsed_op = vars(parsed_op)
    parsed_op.pop("op_name") # op name not needed: inst_type knows its name already
    return inst_type(new_id, **parsed_op)

def createFromPISALine(mem_model: MemoryModel,
                       line: str,
                       line_no: int = 0) -> XInstruction:
    """
    Parses an XInst from the specified string (in P-ISA kernel input format) and returns a
    XInstruction object encapsulating the resulting instruction.

    Note that this function will not decompose P-ISA instructions that require multiple
    XInsts. This function will only match instructions that have a 1:1 equivalent between
    P-ISA and XInst.

    Parameters:
        mem_model (MemoryModel):
            The MemoryModel object, where all variables are kept. Variables parsed from the
            input string will be automatically added to the memory model if they do not already
            exist. The represented object may be modified if addition is needed.
        line (str):
            Line of text containing the instruction to parse in P-ISA kernel input format.
        line_no (int):
            Optional line number for the line. This will be used as ID for the parsed instruction.
            Defaults to 0.

    Returns:
        XInstruction: A XInstruction derived object encapsulating the XInst equivalent to the parsed P-ISA
        instruction or None if line could not be parsed.

    Raises:
        Exception: If an error occurs during parsing, with the line number and content included in the message.
    """

    retval = None

    try:

        for inst_type in __PISA_INSTRUCTIONS:
            parsed_op = inst_type.parseFromPISALine(line)
            if parsed_op:
                assert(inst_type.OP_NAME_PISA == parsed_op.op_name)

                # Convert parsed instruction into an actual instruction object.
                retval = createFromParsedObj(mem_model, inst_type, parsed_op, line_no)

                # Line parsed by an instruction: stop searching.
                break

    except Exception as ex:
        raise Exception(f'line {line_no}: {line}.') from ex

    return retval
