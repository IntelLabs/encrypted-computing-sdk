# MUL - XInst {#mul_XInst}

Element-wise polynomial multiplication.

## Definition

Element-wise multiplication of two polynomials stored in the register file and store the result in a register.

| instr | operand 0 | operand 1 | operand 2 | operand 3 |
|-|-|-|-|-|
| mul | dst | src0 | src1 | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register for result of `src0[i] * src1[i]`. |
| `src0` | register | Source register for first operand. |
| `src1` | register | Source register for second operand. Must be different than `src0`. |
| `res` | int32 | Residue to use for modular reduction |

### Notes

**Uses SPAD-CE data path**: No
