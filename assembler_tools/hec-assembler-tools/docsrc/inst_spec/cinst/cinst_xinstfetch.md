# XINTFETCH - CInst {#xinstfetch_CInst}

Fetches instructions from the HBM and sends it to the XINST queue.

## Definition

Fetches 1 word (32KB) worth of instructions from the HBM XInst region and sends it to the XINST queue.

| instr | operand 0 | operand 1 |
|-|-|-|
| xinstfetch | xq_dst | hbm_src |

## Timing

**Throughput**: 1 clock cycles

**Latency**: Varies

## Details

| Operand | Type | Description |
|-|-|-|
| `xq_dst` | int32 | Dest in XINST queue. |
| `hbm_src` | hbm_addr | Address where to read instructions from HBM XInst region. |

### Notes

**Uses SPAD-CE data path**: No (See CInst [`ifetch`](cinst_ifetch.md))

This instruction is special because it moves XInst data from HBM into XINST queue bypassing SPAD because SPAD is cache only for actual data (not instructions).

Parameter `hbm_src` refers to an HBM address from the XInst region, not the HBM data region.

The destination `xq_dst` indexes the XINST queue word-wise; this is, the 1MB XINST queue capacity is equivalent to 32 words capacity. Thus this parameter is between `0` and `31` and indicates where to load the XInst inside XINST queue.

Instruction `xinstfetch` only loads the XInst to execute, but does not initiate their execution. This is initiated by instruction [`ifetch`](cinst_ifetch.md).

The latency when accessing HBM varies, therefore, there is no specific latency for this instruction.
