# TWNTT - XInst {#twntt_XInst}

Compute twiddle factors for NTT.

## Definition

Performs on-die generation of twiddle factors for the next stage of NTT.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 | operand 5 | operand 6 |
|-|-|-|-|-|-|-|-|
| twntt | dst_tw | src_tw | tw_meta | stage | block | ring_dim | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst_tw` | register | Destination register for resulting twiddles. |
| `src_tw` | register | Source register for original twiddle values. |
| `tw_meta` | int32 | Indexing information of the twiddle metadata. |
| `stage` | int32 | Stage number of the corresponding NTT instruction |
| `block` | int32 | Index of current 16k polynomial chunk. |
| `ring_dim` | int32 | Ring dimension. This is `PMD = 2^ring_dim`, where `PMD` is the poly-modulus degree. |
| `res` | int32 | Residue to use for modular reduction. |

### Notes

**Uses SPAD-CE data path**: No

Both NTT and inverse NTT instructions are defined as one-stage of the transformation. A complete NTT/iNTT transformation is composed of LOG_N such one-stage instructions.
