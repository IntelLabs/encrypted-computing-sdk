# MSTORE - MInst {#mstore_MInst}

Store a single polynomial residue from scratchpad to local memory.

## Definition

Store a word, corresponding to a single polynomial residue, from SPAD memory into HBM data region.

| instr | operand 0 | operand 1 |
|-|-|-|
| mstore | dst | src |

## Timing

**Throughput**: 1 clock cycles

**Latency**: varies

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | hbm_addr | Destination HBM data region address where to store the word. |
| `src` | spad_addr | SPAD address of the word to store. |

### Notes

Latency for read/write times involving HBM vary. CINST queue can use `csyncm` instruction to synchronize with the MINST queue. On the other hand, MINST can use `msyncc` to synchronize with CINST queue.
