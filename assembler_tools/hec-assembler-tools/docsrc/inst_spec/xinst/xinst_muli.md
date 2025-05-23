# MULI - XInst {#muli_XInst}

Element-wise polynomial scaling by an immediate value.

## Definition

Scale a polynomial in the register file by an immediate and store the result in a register.

| instr | operand 0 | operand 1 | operand 2 | operand 3 |
|-|-|-|-|-|
| muli | dst | src0 | imm | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register for result of `src0[i] * imm[i]`. |
| `src0` | register | Source register for first operand. |
| `imm` | string | Named immediate value. |
| `res` | int32 | Residue to use for modular reduction |

### Notes

**Uses SPAD-CE data path**: No
