# MLOAD - MInst {#mload_MInst}

Load a single polynomial residue from local memory to scratchpad.

## Definition

Load a word, corresponding to a single polynomial residue, from HBM data region into the SPAD memory.

| instr | operand 0 | operand 1 |
|-|-|-|
| mload | dst | src |

## Timing

**Throughput**: 1 clock cycles

**Latency**: varies

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | spad_addr | Destination SPAD address where to load the word. |
| `src` | hbm_addr | HBM data region address from where to load. |

### Notes

Latency for read/write times involving HBM vary. CINST queue can use `csyncm` instruction to synchronize with the MINST queue. On the other hand, MINST can use `msyncc` to synchronize with CINST queue.
