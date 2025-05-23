# CSTORE - CInst {#cstore_CInst}

Fetch a single polynomial residue from the intermediate data buffer and store back to SPAD.

## Definition

Pops the top word from the intermediate data buffer queue and stores it in SPAD.

| instr | operand 0 |
|-|-|
| cstore | dst |

## Timing

**Throughput**: 1 clock cycles*

**Latency**: 1 clock cycles*

Variable timing because `cstore` is a blocking instruction. See notes.

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | spad_addr | Destination SPAD address where to store the word. |

### Notes

**Uses SPAD-CE data path**: No (see XInst [`xstore`](../xinst/xinst_xstore.md) ).

This instruction will pop the word at the top of the intermediate buffer queue where Xinst `xstore` pushes data to store from CE registers.

WARNING: If the intermediate buffer is empty, `cstore` blocks the CINST queue execution until there is data ready to pop. Produced code must ensure that there is data in the intermediate buffer, or that there will be a matching `xstore` in the bundle being executed to avoid a deadlock.

## See Also

- CInst [`xstore`](../xinst/xinst_xstore.md)
