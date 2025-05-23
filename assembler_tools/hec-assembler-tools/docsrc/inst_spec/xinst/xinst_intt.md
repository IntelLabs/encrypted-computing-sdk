# iNTT - XInst {#intt_XInst}

Inverse Number Theoretic Transform. Convert NTT form to positional form.

## Definition

Performs one-stage of inverse NTT.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 | operand 5 | operand 6 |
|-|-|-|-|-|-|-|-|
| intt | dst_top | dest_bot | src_top | src_bot | src_tw | stage | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst_top` | register | Destination register for top part of the iNTT result. |
| `dst_bot` | register | Destination register for bottom part of the iNTT result. Must be different than `dst_top`. |
| `src_top` | register | Source register for top part of the input NTT. |
| `src_bot` | register | Source register for bottom part of the input NTT. Must be different than `src_top`. |
| `src_tw` | register | Source register for twiddle factors. Must be different than `src_top` and `src_bot`. |
| `stage` | int32 | Stage number of the current iNTT instruction. |
| `res` | int32 | Residue to use for modular reduction. |

### Notes

**Uses SPAD-CE data path**: No

Both NTT and inverse NTT instructions are defined as one-stage of the transformation. A complete NTT/iNTT transformation is composed of LOG_N such one-stage instructions.

This instruction matches to HERACLES ISA `intt`. It requires a preceeding, matching [`rmove`](xinst_rmove.md) to shuffle the input bits into correct tile-pairs.
