import networkx as nx
from assembler.memory_model.variable import Variable

def buildVarAccessListFromTopoSort(dependency_graph: nx.DiGraph):
    """
    Given the dependency directed acyclic graph of XInsts, builds the list of
    estimated usage order for the variables.

    This is used when deciding which variable to evict from register files or SPAD when
    a memory location is needed and all are occupied (furthest used: FTBU). Least recently
    used (LRU) is used as tie breaker.

    Usage order is estimated because order of instructions may change based on their
    dependencies and timings during scheduling.

    Returns:
        list(instruction_id: tuple):
            The topological sort of the instructions. Since the topological sort is required
            for this function, it is returned to caller to be reused if needed.
    """

    topo_sort = list(nx.topological_sort(dependency_graph))
    for idx, node in enumerate(topo_sort):
        instr = dependency_graph.nodes[node]['instruction']
        vars = set(instr.sources + instr.dests)
        for v in vars:
            v.accessed_by_xinsts.append(Variable.AccessElement(idx, instr.id))

    return topo_sort
