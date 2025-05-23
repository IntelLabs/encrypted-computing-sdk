# RSHUFFLE - XInst {#rshuffle_XInst}

Shuffles/routes NTT/iNTT outputs/inputs across tile pairs.

## Definition

Shuffles two register locations among the tile pairs, based on destinations defined by currently loaded routing table metadata.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 | operand 5 |
|-|-|-|-|-|-|-|
| rshuffle | dst0 | dst1 | src0 | src1 | wait_cyc | data_type |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 23 clock cycles

**Special Latency**:

| data_type | latency |
|-|-|
| `ntt` | 5*`n` or 17 clock cycles |
| `intt` | 5*`n` or 17 clock cycles |

### Restrictions

Hardware resources are tied up for each `rshuffle`. Behavior when attempting to execute another `rshuffle` in the pipeline before the corresponding latency elapses is undefined.

- Two `rshuffle` instructions with the same `data_type` cannot overlap on *special latency*. This is: `rshuffle` instructions must be scheduled at multiples of 5 clock cycle intervals (up to 15 cycles) or at 17 or greater clock cycles from each other to avoid resource contention.
- Two `rshuffle` instructions with different `data_type` cannot execute in the same bundle as there is only one routing table metadata available.

Any other XInstruction can overlap with `rshuffle`. However, no XInstruction that writes to the same banks as an `rshuffle` can end in the same cycle of said `rshuffle`.

Instruction `rshuffle` will overwrite the contents of its output registers on its last cycle of latency. Values written to these same registers by any other XInstruction before `rshuffle` completes, will be overwritten at this time.

## Details

| Operand | Type | Description |
|-|-|-|
| `dst0` | register | Destination register where to shuffle `src0`. |
| `dst1` | register | Destination register where to shuffle `src1`. Must be different than `dst0`. |
| `src0` | register | Source register to shuffle. |
| `src1` | register | Source register to shuffle. Must be different than `src0`. |
| `wait_cyc` | int32 | Not used. Set to `0`. |
| `data_type` | string | One of [`ntt`, `intt`] to indicate the type of shuffling depending on the corresponding matching operation. See notes. |

### Notes

**Uses SPAD-CE data path**: No

This instruction is mostly intended to shuffle values in registers among tile-pairs (akin to bit shuffling). Due to the nature of NTT and iNTT butterflies, their respective outputs and inputs are shuffled among tile-pairs by the mathematical operations. This instruction is intended to re-shuffle the outputs from an NTT or inputs for an iNTT into the correct bit order.

The typical usage to shuffle the tile-pairs of NTT outputs is as such:

```csv
ntt, dst_top, dst_bot, src_top, src_bot, src_tw, stage, res # SL=1
nop 4 # dependency latency for ntt results
rshuffle, dst_top, dst_bot, dst_top, dst_bot, 0, ntt
```

Notice that while `rshuffle`'s source and destination registers are the same in the example above, the actual contents will be shuffled among the tile-pairs.

The typical usage to shuffle the tile-pairs of iNTT inputs is as such:

```csv
rshuffle, src_top, src_bot, src_top, src_bot, 0, intt
nop 21 # dependency latency for rshuffle results
intt, dst_top, dest_bot, src_top, src_bot, src_tw, stage, res
```

Notice that while `rshuffle`'s source and destination registers are the same in the example above, the actual contents will be shuffled among the tile-pairs.

Routing table metadata defining shuffling patterns is loaded by [`nload`](../cinst/cinst_nload.md).

Parameter `data_type` is intended to select the correct routing table, however, in the current HERACLES implementation, only one routing table is availabe, and this parameter is used only for book keeping and error detection during scheduling.
