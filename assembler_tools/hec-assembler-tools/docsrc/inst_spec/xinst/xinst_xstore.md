# XSTORE - XInst {#xstore_XInst}

Transfers data from a register into the intermediate data buffer for subsequent transfer into SPAD.

## Definition

Transfers a word from a CE register into the intermediate data buffer. The intermediate data buffer features a FIFO structure, which means that the transferred data is pushed at the end of the queue.

| instr | operand 0 |
|-|-|
| xstore | src |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 4 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `src` | register | Source register to store into SPAD. |

### Notes

**Uses SPAD-CE data path**: Yes

This instruction pushes data blindly into the intermediate data buffer in a LIFO structure. It is the responsibility of the CINST execution queue to pop this data buffer timely, via `cstore` instruction, to avoid overflows.

The data will be ready in the intermediate data buffer queue one clock cycle after `xstore` completes. Writing to the `src` register during `xstore` is undefined.

## See Also

- CInst [`cstore`](../cinst/cinst_cstore.md)
- CInst [`cload`](../cinst/cinst_cload.md)
