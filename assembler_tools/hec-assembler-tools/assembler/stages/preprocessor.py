import networkx as nx

from assembler.common.constants import Constants
from assembler.instructions import xinst
from assembler.instructions.xinst.xinstruction import XInstruction
from assembler.instructions.xinst import parse_xntt
from assembler.memory_model import MemoryModel
from assembler.memory_model import variable

def __dependencyGraphForVars(insts_list: list) -> (nx.Graph, set, set):
    """
    Given the listing of instructions, this method returns the dependency graph
    for the variables in the listing and the sets of destination and source variables.

    Parameters:
        insts_list (list): List of corresponding pre-processed P-ISA instructions containing the variables
                           to process.

    Returns:
        tuple: A tuple containing:
            - nx.Graph: Dependency graph for the variables in the listing.
                Nodes: variable names.
                Edges: dependencies among variables.
                Dependencies:
                    - All variables being read from at the same time in any one instruction
                      depend on each other because it is forbidden to read more than once from
                      the same register bank in the same instruction.
                    - All variables being written to at the same time in any one instruction
                      depend on each other because it is forbidden to write more than once to
                      the same register bank in one instruction.
            - set: Set of all variables (name) that are destinations in the input `insts_list`.
            - set: Set of all variables (name) that are sources in the input `insts_list`.
    """
    retval = nx.Graph()
    all_dests_vars = set()
    all_sources_vars = set()

    for inst in insts_list:
        extra_sources = []
        for idx, v in enumerate(inst.dests):
            all_dests_vars.add(v.name)
            if v.name not in retval:
                retval.add_node(v.name)
            for v_i in range(idx + 1, len(inst.dests)):
                v_next = inst.dests[v_i]
                if v.name == v_next.name:
                    raise RuntimeError(f"Cannot write to the same variable in the same instruction more than once: {inst.toPISAFormat()}")
                if not retval.has_edge(v.name, v_next.name):
                    retval.add_edge(v.name, v_next.name)
            # Mac deps already handled in the Mac instructions themselves
            # if isinstance(inst, (xinst.Mac, xinst.Maci)):
            #     extra_sources.append(v)

        inst_all_sources = extra_sources + inst.sources
        for idx, v in enumerate(inst_all_sources):
            all_sources_vars.add(v.name)
            if v.name not in retval:
                retval.add_node(v.name)
            for v_i in range(idx + 1, len(inst_all_sources)):
                v_next = inst_all_sources[v_i]
                if v.name == v_next.name:
                    raise RuntimeError(f"Cannot read from the same variable in the same instruction more than once: {inst.toPISAFormat()}")
                if not retval.has_edge(v.name, v_next.name):
                    retval.add_edge(v.name, v_next.name)

    return retval, all_dests_vars, all_sources_vars

def injectVariableCopy(mem_model: MemoryModel,
                       insts_list: list,
                       instruction_idx: int,
                       var_name: str) -> int:
    """
    Injects a copy of a variable into the instruction list at the specified index.

    Parameters:
        mem_model (MemoryModel): The memory model containing the variables.
        insts_list (list): The list of instructions.
        instruction_idx (int): The index at which to inject the copy.
        var_name (str): The name of the variable to copy.

    Returns:
        int: Index for the instruction in the list after injection.

    Raises:
        IndexError: If the instruction index is out of range.
    """
    if instruction_idx < 0 or instruction_idx >= len(insts_list):
        raise IndexError(f'instruction_idx: Expected index in range [0, {len(insts_list)}), but received {instruction_idx}.')
    last_instruction: XInstruction = insts_list[instruction_idx]
    last_instruction_sources = last_instruction.sources[:]
    for idx, variable in enumerate(last_instruction_sources):
        if variable.name == var_name:
            # Find next available temp var name
            temp_name = mem_model.findUniqueVarName()
            temp_var = mem_model.retrieveVarAdd(temp_name, -1)
            # Copy source var into temp
            copy_xinst = xinst.Copy(id = last_instruction.id[1],
                                    N = 0,
                                    dst = [ temp_var ],
                                    src = [ variable ],
                                    comment='Injected copy for bank reduction.')
            insts_list.insert(instruction_idx, copy_xinst)
            # Replace src by temp
            last_instruction.sources[idx] = temp_var
            instruction_idx += 1

    return instruction_idx

def reduceVarDepsByVar(mem_model: MemoryModel,
                       insts_list: list,
                       var_name: str):
    """
    Reduces variable dependencies by injecting copies of the specified variable.

    Parameters:
        mem_model (MemoryModel): The memory model containing the variables.
        insts_list (list): The list of instructions.
        var_name (str): The name of the variable to reduce dependencies for.
    """
    last_pos = 0
    last_instruction = None
    # Find all instructions* with specified variable and make it a copy
    # * care with mac instructions
    while last_pos < len(insts_list):
        if var_name in (v.name for v in insts_list[last_pos].sources):
            last_instruction: XInstruction = insts_list[last_pos]
            if isinstance(last_instruction, (xinst.Mac, xinst.Maci)):
                # Check if the conflicting variable is the accumulator
                if last_instruction.sources[0].name == var_name:
                    # Turn all other variables into copies
                    for variable in last_instruction.sources[1:]:
                        last_pos = injectVariableCopy(mem_model, insts_list, last_pos, variable.name)
                        assert last_instruction == insts_list[last_pos]
                    last_instruction = None # avoid further processing of instruction
                    last_pos += 1
                    continue
                # If conflict variable was not the accumulator, proceed to change the other variables
            # Skip copy, twxntt and xrshuffle
            if not isinstance(last_instruction, (xinst.twiNTT,
                                                 xinst.twiNTT,
                                                 xinst.irShuffle,
                                                 xinst.rShuffle,
                                                 xinst.Copy)):
                # Break up indicated variable in sources into a temp copy
                last_pos = injectVariableCopy(mem_model, insts_list, last_pos, var_name)
                assert last_instruction == insts_list[last_pos]

        last_pos += 1

def assignRegisterBanksToVars(mem_model: MemoryModel,
                              insts_list: list,
                              use_bank0: bool,
                              verbose = False) -> str:
    """
    Assigns register banks to variables using vertex coloring graph algorithm.

    The variables contained in the MemoryModel object will be modified to reflect
    their suggested bank.

    Parameters:
        mem_model (MemoryModel): The MemoryModel object, where all variables are kept. Variables detected that are
                                 not already in the MemoryModel collection of variables will be added automatically.
                                 The variables contained in the MemoryModel object will be modified to reflect
                                 their suggested bank.
        insts_list (list): List of corresponding pre-processed P-ISA instructions containing the variables
                           to process.
        use_bank0 (bool): All variables are written into registers in bank 0 from SPAD, while no XInst
                          should be writing its results in bank 0 to avoid write-write conflicts.
                          If `True`, variables that can remain in bank 0 will be kept there (variables
                          that are never written to).
                          If `False`, bank 0 will not be assigned to any variable. Resulting ASM instructions
                          should add corresponding `move` instructions to move variables from bank 0 to
                          correct bank.
        verbose (bool, optional): If True, prints verbose output. Defaults to False.

    Raises:
        ValueError: Thrown for these cases:
            - Invalid input values for parameters.
            - Variables in listing cannot be successfully assigned to banks (the number
              of banks is insufficient to accommodate the listing given the rules).
              This should not happen, as long as rules are respected, and all instructions
              have, at most, 3 inputs, and at most, 3 outputs.

    Returns:
        str: The unique dummy variable name that was not used by the collection of variables in the
             instruction listing.
    """
    reduced_vars = set()
    needs_reduction = True
    pass_counter = 0
    while needs_reduction:
        pass_counter += 1
        if verbose:
            print(f"Pass {pass_counter}")
        # Extract the dependency graph for variables
        dep_graph_vars, dest_names, source_names = __dependencyGraphForVars(insts_list)
        only_sources = source_names - dest_names # Find which variables are ever only used as sources
        color_dict = nx.greedy_color(dep_graph_vars) # Do coloring

        needs_reduction = False
        for var_name, bank in color_dict.items():
            if bank > 2:
                if var_name in reduced_vars:
                    raise RuntimeError(('Found invalid bank {} > 2 for variable {} already reduced.').format(bank,
                                                                                                             var_name))
                # DEBUG print
                if verbose:
                    print('Variable {} ({}) requires reduction.'.format(var_name, bank))
                reduceVarDepsByVar(mem_model, insts_list, var_name)
                reduced_vars.add(var_name) # Track reduced variable
                needs_reduction = True

    # Assign banks based on coloring algo results
    for v in mem_model.variables.values():
        if not mem_model.isMetaVar(v.name): # Skip meta variables
            assert(v.name in color_dict)
            bank = color_dict[v.name]
            assert bank < 3, f'{v.name}, {bank}'
            # If requested, keep vars used only as sources in bank 0
            v.suggested_bank = bank + (0 if use_bank0 and (v.name in only_sources) else 1)

    retval: str = mem_model.findUniqueVarName()

    return retval

def preprocessPISAKernelListing(mem_model: MemoryModel,
                                line_iter,
                                progress_verbose: bool = False) -> list:
    """
    Parses a P-ISA kernel listing, given as an iterator for strings, where each is
    a line representing a P-ISA instruction.

    Generates twiddle factors and bit shuffling for original P-ISA xntt instructions.

    Variables in `mem_model` associated with the output will have assigned banks automatically.

    Parameters:
        mem_model (MemoryModel): The MemoryModel object, where all variables are kept. Variables parsed from the
                                 input string will be automatically added to the memory model if they do not already
                                 exist. The represented object may be modified if addition is needed.
        line_iter (iterator): Iterator of strings where each is a line of the P-ISA kernel instruction listing.
        progress_verbose (bool, optional): Specifies whether to output progress every hundred lines processed to stdout.
                                           Defaults to False.

    Returns:
        list: A list of `BaseInstruction`s where each object represents
              the a parsed instruction. Some P-ISA instructions (such as ntts) are converted into
              a group of XInst that implement the original P-ISA instruction.

              Variables in `mem_model` collection of variables will be modified to reflect
              assigned bank in `suggested_bank` attribute.
    """
    NTT_KERNEL_GRAMMAR = lambda line: parse_xntt.parseXNTTKernelLine(line, xinst.NTT.OP_NAME_PISA, Constants.TW_GRAMMAR_SEPARATOR)
    iNTT_KERNEL_GRAMMAR = lambda line: parse_xntt.parseXNTTKernelLine(line, xinst.iNTT.OP_NAME_PISA, Constants.TW_GRAMMAR_SEPARATOR)

    retval = []

    if progress_verbose:
        print("0")
    num_input_insts = 0
    for line_no, s_line in enumerate(line_iter, 1):
        num_input_insts = line_no
        if progress_verbose and line_no % 100 == 0:
            print(f"{num_input_insts}")

        parsed_insts = None
        if not parsed_insts:
            parsed_op = NTT_KERNEL_GRAMMAR(s_line)
            if not parsed_op:
                parsed_op = iNTT_KERNEL_GRAMMAR(s_line)
            if parsed_op:
                # Instruction is a P-ISA xntt
                parsed_insts = parse_xntt.generateXNTT(mem_model,
                                                       parsed_op,
                                                       new_id = line_no)
        if not parsed_insts:
            # Instruction is one that is represented by single XInst
            inst = xinst.createFromPISALine(mem_model, s_line, line_no)
            if inst:
                parsed_insts = [ inst ]

        if not parsed_insts:
            raise SyntaxError("Line {}: unable to parse kernel instruction:\n{}".format(line_no, s_line))

        retval += parsed_insts

    if progress_verbose:
        print(f"{num_input_insts}")

    return retval