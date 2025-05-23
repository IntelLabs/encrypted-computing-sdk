# MACI - XInst {#maci_XInst}

Element-wise polynomial scaling by an immediate value and accumulation.

## Definition

Scale a polynomial in the register file by an immediate added to a third polynomial stored in a register, and store the result in a register.

| instr | operand 0 | operand 1 | operand 2 | operand 3 | operand 4 |
|-|-|-|-|-|-|
| maci | dst | src0 | src1 | imm | res |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register for result of `src1[i] * imm[i] + src0[i]`. |
| `src0` | register | Source register for first operand. Must be same as `dst`. |
| `src1` | register | Source register for second operand. Must be different than `src0`. |
| `imm` | string | Named immediate value. |
| `res` | int32 | Residue to use for modular reduction |

### Notes

**Uses SPAD-CE data path**: No
