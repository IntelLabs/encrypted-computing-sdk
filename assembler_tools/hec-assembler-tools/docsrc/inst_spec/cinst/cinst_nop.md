# NOP - CInst {#nop_CInst}

Adds desired amount of idle cycles in the Cfetch flow.

## Definition

Introduces idle cycles in the CINST execution flow.

| instr | operand 0 |
|-|-|
| cnop | cycles |

## Timing

**Throughput**: `1 + cycles` clock cycles

**Latency**: `1 + cycles` clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `cycles` | int, 10bits | Number of idle cycles to introduce (see notes). |

### Notes

**Uses SPAD-CE data path**: No

Note that this instruction will cause the compute flow to stall for `1 + cycles` since it takes 1 clock cycle to dispatch the instruction. Therefore, to introduce a single idle cycle, the correct instruction is:

```
cnop, 0
```

Parameter `cycles` is encoded into a 10 bits field, and thus, its value must be less than 1024. If more thatn 1024 idle cycles is required, multiple `cnop` instructions must be scheduled back to back.
