# SUB - XInst {#sub_XInst}

Element-wise polynomial subtraction.

## Definition

Add two polynomials stored in the register file and store the result in a register.

| instr | operand 0 | operand 1 | operand 2 | operand 3 |
|-|-|-|-|-|
| sub | dst | src0 | src1 | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register for result of `src0 - src1`. |
| `src0` | register | Source register for first operand. |
| `src1` | register | Source register for second operand. Must be different than `src0`. |
| `res` | int32 | Residue to use for modular reduction |

### Notes

**Uses SPAD-CE data path**: No
