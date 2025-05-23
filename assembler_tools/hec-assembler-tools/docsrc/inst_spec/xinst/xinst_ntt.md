# NTT - XInst {#ntt_XInst}

Number Theoretic Transform. Convert positional form to NTT form.

## Definition

Performs one-stage of NTT on an input positional polynomial.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 | operand 5 | operand 6 |
|-|-|-|-|-|-|-|-|
| ntt | dst_top | dest_bot | src_top | src_bot | src_tw | stage | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst_top` | register | Destination register for top part of the NTT result. |
| `dst_bot` | register | Destination register for bottom part of the NTT result. Must be different than `dst_top`. |
| `src_top` | register | Source register for top part of the input polynomial. |
| `src_bot` | register | Source register for bottom part of the input polynomial. Must be different than `src_top`. |
| `src_tw` | register | Source register for original twiddle factors. Must be different than `src_top` and `src_bot`. |
| `stage` | int32 | Stage number of the current NTT instruction. |
| `res` | int32 | Residue to use for modular reduction. |

### Notes

**Uses SPAD-CE data path**: No

Both NTT and inverse NTT instructions are defined as one-stage of the transformation. A complete NTT/iNTT transformation is composed of LOG_N such one-stage instructions.

This instruction matches to HERACLES ISA `ntt` with `store_local` bit set. i.e. it requires a subsequent, matching [`rmove`](xinst_rmove.md) to shuffle the output bits into correct tile-pairs.
