# BONES - CInst {#bones_CInst}

Load metadata of identity (one) from scratchpad to register file.

## Definition

Loads metadata of identity representation for cryptographic operations from scratchpad to special registers in register file.

| instr | operand 0 | operand 1 |
|-|-|-|
| bones | spad_src | col_num |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 5 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `spad_src` | spad_addr | SPAD address of identity metadata to load. |
| `col_num` | int32 | Block to load from source word. Must be `0` |

### Notes

**Uses SPAD-CE data path**: Yes

The metadata block for identity is always `0`.

Some operations require metadata to indicate parameters and modes of operation that don't change throughout the execution of the program. Metadata is loaded once at the start of the program into special registers in the CE.
