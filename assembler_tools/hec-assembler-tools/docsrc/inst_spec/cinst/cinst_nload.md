# NLOAD - CInst {#nload_CInst}

Loads NTT/iNTT routing mapping data.

## Definition

Loads metadata (for NTT/iNTT routing mapping) from scratchpad into a special routing table register.

| instr | operand 0 | operand 1 |
|-|-|-|
| nload | table_idx_dst | spad_src |

## Timing

**Throughput**: 4 clock cycles

**Latency**: 4 clock cycless

## Details

| Operand | Type | Description |
|-|-|-|
| `table_idx_dst` | int32 | Destination routing table. Must be in range `[0, 6)` as there are 6 possible routing tables. |
| `spad_src` | spad_addr | SPAD address of metadata variable to load. |

### Notes

**Uses SPAD-CE data path**: Yes

This instruction loads metadata indicating how will [`rshuffle`](../xinst/xinst_rshuffle.md) instruction shuffle tile pair registers for NTT outputs and iNTT inputs. Shuffling for one of these instructions requires two tables: routing table and auxiliary table. Therefore, the 6 special table registers only support 3 different shuffling operations (NTT, iNTT, and MISC).

In the current HERACLES implementation, only routing tables `0` and `1` are functional, thus, assembler is able to perform only shuffling instructions for one of NTT or iNTT per bundle, requiring routing table changes whenever the other is needed.
