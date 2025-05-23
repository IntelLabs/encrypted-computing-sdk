import warnings

from argparse import Namespace

from assembler.common import constants
from assembler.instructions import xinst
from assembler.memory_model import MemoryModel

__xntt_id = 0

def parseXNTTKernelLine(line: str,
                        op_name: str,
                        tw_separator: str) -> Namespace:
    """
    Parses an `xntt` instruction from a P-ISA kernel instruction string.

    Parameters:
        line (str): The line containing the instruction to parse.
                    Instruction format: N, op_name, dst0, dst1, src0, src1, twiddle, res # comment
                    Comment is optional.

        op_name (str): The operation name that should be contained in the line.

        tw_separator (str): The separator used in the twiddle information.

    Returns:
        Namespace: A namespace with the following attributes:
            N (int): Ring size = Log_2(PMD)
            op_name (str): Operation name
            dst (list of tuple): List of destinations of the form (variable_name, suggested_bank).
            src (list of tuple): List of sources of the form (variable_name, suggested_bank).
            res (int): Residual for the operation.
            stage (int): Stage number of the current NTT instruction.
            block (int): Index of current word in the 2-words (16KB) polynomial.
            comment (str): String with the comment attached to the line (empty string if no comment).

        None: If an `xntt` could not be parsed from the input.
    """

    OP_NUM_DESTS   = 2
    OP_NUM_SOURCES = 2
    OP_NUM_TOKENS  = 8

    retval = None
    tokens = xinst.XInstruction.tokenizeFromPISALine(op_name, line)
    if tokens:
        retval = {"comment": tokens[1]}
        instr_tokens = tokens[0]

        if len(instr_tokens) > OP_NUM_TOKENS:
            warnings.warn(f'Extra tokens detected for instruction "{op_name}"', SyntaxWarning)

        retval["N"] = int(instr_tokens[0])
        retval["op_name"] = instr_tokens[1]
        params_start = 2
        params_end = params_start + OP_NUM_DESTS + OP_NUM_SOURCES
        dst_src = xinst.XInstruction.parsePISASourceDestsFromTokens(instr_tokens,
                                                                    OP_NUM_DESTS,
                                                                    OP_NUM_SOURCES,
                                                                    params_start)
        retval.update(dst_src)
        twiddle = instr_tokens[params_end]
        retval["res"] = int(instr_tokens[params_end + 1])

        # Parse twiddle (w_<res>_<stage>_<block>, where "_" is the `tw_separator`)
        twiddle_tokens = list(map(lambda s: s.strip(), twiddle.split(tw_separator)))
        if len(twiddle_tokens) != 4:
            raise ValueError(f'Error parsing twiddle information for "{op_name}" in line "{line}".')
        if twiddle_tokens[0] != "w":
            raise ValueError(f'Invalid twiddle detected for "{op_name}" in line "{line}".')
        if int(twiddle_tokens[1]) != retval["res"]:
            raise ValueError(f'Invalid "residual" component detected in twiddle information for "{op_name}" in line "{line}".')
        retval["stage"] = int(twiddle_tokens[2])
        retval["block"] = int(twiddle_tokens[3])

        retval = Namespace(**retval)
        assert(retval.op_name == op_name)
    return retval

def __generateRMoveParsedOp(kntt_parsed_op: Namespace) -> (type, Namespace):
    """
    Generates a namespace compatible with xrshuffle XInst constructor.

    Parameters:
        kntt_parsed_op (Namespace): Parsed xntt object (Namespace).

    Returns:
        tuple: A tuple containing the xrshuffle type and a Namespace with the parsed operation.
    """
    xrshuffle_type = None
    parsed_op = {}
    parsed_op["N"] = kntt_parsed_op.N
    parsed_op["op_name"] = ""
    parsed_op["wait_cyc"] = 0
    parsed_op["dst"] = []
    parsed_op["src"] = []
    parsed_op["comment"] = ""

    if kntt_parsed_op.op_name == xinst.NTT.OP_NAME_PISA:
        xrshuffle_type = xinst.rShuffle
        parsed_op["dst"] = [d for d in kntt_parsed_op.dst]
    elif kntt_parsed_op.op_name == xinst.iNTT.OP_NAME_PISA:
        xrshuffle_type = xinst.irShuffle
        parsed_op["dst"] = [s for s in kntt_parsed_op.src]
    else:
        raise ValueError('`kntt_parsed_op`: cannot process operation with name "{}".'.format(kntt_parsed_op.op_name))

    assert(xrshuffle_type)

    parsed_op["src"] = parsed_op["dst"]
    parsed_op["op_name"] = xrshuffle_type.OP_NAME_PISA

    # rshuffle goes above corresponding intt or below corresponding ntt
    return xrshuffle_type, Namespace(**parsed_op)

def __generateTWNTTParsedOp(xntt_parsed_op: Namespace) -> Namespace:
    """
    Generates a namespace compatible with twxntt XInst constructor.

    Parameters:
        xntt_parsed_op (Namespace): Parsed kernel xntt object (Namespace).

    Returns:
        tuple: A tuple containing the twxntt type, a Namespace with the parsed operation, and a tuple with the twiddle variable name and suggested bank.
               The twxntt type is None if a twxntt is not needed for the specified xntt.
    """
    global __xntt_id # TODO: replace by unique ID once it gets integrated into the P-ISA kernel.

    retval = None

    parsed_op = {}
    parsed_op["N"] = xntt_parsed_op.N
    parsed_op["op_name"] = 'tw' + str(xntt_parsed_op.op_name)
    parsed_op["res"] = xntt_parsed_op.res
    parsed_op["stage"] = xntt_parsed_op.stage
    parsed_op["block"] = xntt_parsed_op.block
    parsed_op["dst"] = []
    parsed_op["src"] = []
    parsed_op["tw_meta"] = 0
    parsed_op["comment"] = ""

    # Find types depending on whether we are doing ntt or intt
    twxntt_type = next((t for t in (xinst.twNTT, xinst.twiNTT) if t.OP_NAME_PISA == parsed_op["op_name"]), None)
    assert(twxntt_type)

    # Adapted from legacy code add_tw_xntt
    #-------------------------------------

    ringsize = int(parsed_op["N"])
    rminustwo = ringsize - 2
    rns_term = int(parsed_op["res"])
    stage = int(parsed_op["stage"])

    # Generate meta data look-up
    meta_rns_term = rns_term % constants.MemoryModel.MAX_RESIDUALS
    mdata_word_sel = meta_rns_term >> 1 # 5bit word select
    mdata_inword_res_sel = meta_rns_term & 1
    mdata_inword_stage_sel = rminustwo - stage
    if twxntt_type == xinst.twiNTT:
        mdata_inword_ntt_sel = 1 # Select intt field
    else: # xinst.twNTT
        mdata_inword_ntt_sel = 0 # Select ntt field
    mdata_ptr = (mdata_word_sel << 6)
    mdata_ptr |= (mdata_inword_res_sel << 5)
    mdata_ptr |= (mdata_inword_ntt_sel << 4)
    mdata_ptr |= mdata_inword_stage_sel

    block = int(parsed_op["block"])

    if rns_term == 0 and stage == 0 and block == 0:
        __xntt_id += 1

    # Generate twiddle variable name
    tw_var_name_bank = ("w_gen_{}_{}_{}_{}".format(mdata_inword_ntt_sel, __xntt_id, rns_term, block), 1)

    meta_data_comment  = "{} {} ".format(mdata_word_sel, mdata_inword_res_sel)
    meta_data_comment += "{} {} w_{}_{}_{}".format(mdata_inword_ntt_sel, mdata_inword_stage_sel,
                                                   # hop_list[6]
                                                   parsed_op["res"], parsed_op["stage"], parsed_op["block"])

    parsed_op["dst"] = [tw_var_name_bank]
    parsed_op["src"] = [tw_var_name_bank]
    parsed_op["tw_meta"] = mdata_ptr
    parsed_op["comment"] = meta_data_comment

    if twxntt_type == xinst.twNTT and mdata_ptr >= 0:
        # NTT
        retval = twxntt_type
    elif twxntt_type == xinst.twiNTT and stage <= rminustwo:
        # iNTT
        # Only add twiddle inst in lower stages
        retval = twxntt_type
    # else None

    return retval, Namespace(**parsed_op), tw_var_name_bank

def generateXNTT(mem_model: MemoryModel,
                 xntt_parsed_op: Namespace,
                 new_id: int = 0) -> list:
    """
    Parses an `xntt` instruction from a P-ISA kernel instruction string.

    Parameters:
        mem_model (MemoryModel): The MemoryModel object, where all variables are kept. Variables parsed from the
                                 input string will be automatically added to the memory model if they do not already
                                 exist. The represented object may be modified if addition is needed.

        xntt_parsed_op (Namespace): Namespace of parsed xntt from P-ISA.

        new_id (int, optional): A new ID for the instruction. Defaults to 0.

    Returns:
        list: A list of `xinstruction.XInstruction` representing the instructions needed to compute the
              parsed xntt.
    """
    retval = []

    # Find xntt type depending on whether we are doing ntt or intt
    xntt_type = next((t for t in (xinst.NTT, xinst.iNTT) if t.OP_NAME_PISA == xntt_parsed_op.op_name), None)
    if not xntt_type:
        raise ValueError('`xntt_parsed_op`: cannot process parsed kernel operation with name "{}".'.format(xntt_parsed_op.op_name))

    # Generate twiddle instruction
    #-----------------------------

    twxntt_type, twxntt_parsed_op, last_twxinput_name = __generateTWNTTParsedOp(xntt_parsed_op)
    # print(twxntt_parsed_op)
    twxntt_inst = None
    if twxntt_type:
        twxntt_inst = xinst.createFromParsedObj(mem_model, twxntt_type, twxntt_parsed_op, new_id)

    # Generate corresponding rshuffle
    #-----------------------------

    rshuffle_type, rshuffle_parsed_op = __generateRMoveParsedOp(xntt_parsed_op)
    rshuffle_parsed_op.comment += (" " + twxntt_parsed_op.comment) if twxntt_parsed_op else ""
    rshuffle_inst = xinst.createFromParsedObj(mem_model, rshuffle_type, rshuffle_parsed_op, new_id)

    # Generate xntt instruction
    #--------------------------

    # Prepare arguments for ASM ntt instruction object construction
    if twxntt_parsed_op:
        assert(twxntt_parsed_op.stage == xntt_parsed_op.stage)
    delattr(xntt_parsed_op, "block")
    xntt_parsed_op.src.append(last_twxinput_name)
    xntt_parsed_op.comment += twxntt_parsed_op.comment if twxntt_parsed_op else ""

    # Create instruction
    xntt_inst = xinst.createFromParsedObj(mem_model, xntt_type, xntt_parsed_op, new_id)

    # Add instructions to return list
    #--------------------------------

    retval = [xntt_inst] # xntt

    if xntt_type == xinst.iNTT: # rshuffle
        # rshuffle goes above corresponding intt
        retval = [rshuffle_inst] + retval
    else:
        # rshuffle goes below corresponding ntt
        retval.append(rshuffle_inst)

    if twxntt_inst: # twiddle
        retval.append(twxntt_inst)

    return retval