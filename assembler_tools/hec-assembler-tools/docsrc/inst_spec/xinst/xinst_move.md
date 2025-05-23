# MOVE - XInst {#move_XInst}

Copies data from one register to a different one.

## Definition

Copies data from a source register into a different destination register.

| instr | operand 0 | operand 1 |
|-|-|-|
| move | dst | src |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 6 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register. |
| `src` | register | Source register to copy. Must be different than `dst`, but can be in the same bank. |

### Notes

**Uses SPAD-CE data path**: No
