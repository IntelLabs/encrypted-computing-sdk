# NOP - XInst {#nop_XInst}

Adds desired amount of idle cycles to the compute flow.

## Definition

Introduces idle cycles in the compute engine.

| instr | operand 0 |
|-|-|
| nop | cycles |

## Timing

**Throughput**: `1 + cycles` clock cycles

**Latency**: `1 + cycles` clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `cycles` | int32 | Number of idle cycles to introduce (see notes). |

### Notes

**Uses SPAD-CE data path**: No

Note that this instruction will cause the compute flow to stall for `1 + cycles` since it takes 1 clock cycle to dispatch the instruction. Therefore, to introduce a single idle cycle, the correct instruction is:

```
nop, 0
```
