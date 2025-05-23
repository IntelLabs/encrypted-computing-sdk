# MAC - XInst {#mac_XInst}

Element-wise polynomial multiplication and accumulation.

## Definition

Element-wise multiplication of two polynomials added to a third polynomial, all stored in the register file, and store the result in a register.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 |
|-|-|-|-|-|-|
| mac | dst | src0 | src1 | src2 | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register for result of `src1[i] * src2[i] + src0[i]`. |
| `src0` | register | Source register for first operand. Must be the same as `dst`. |
| `src1` | register | Source register for second operand. Must be different than `src0`. |
| `src2` | register | Source register for third operand. Must be different than `src0` and `src1`. |
| `res` | int32 | Residue to use for modular reduction |

### Notes

**Uses SPAD-CE data path**: No
