# CSYNCM - CInst {#csyncm_CInst}

CINST execution waits for a particular Mfetch instruction to complete.

## Definition

Wait instruction similar to a barrier that stalls the execution of CINST queue until the specified instruction from MINST queue has completed.

| instr | operand 0 |
|-|-|
| csyncm | inst_num |

## Timing

**Throughput**: varies

**Latency**: Same as throughput.

## Details

| Operand | Type | Description |
|-|-|-|
| `inst_num` | int32 | Instruction number from the MINST queue for which to wait. |

### Notes

**Uses SPAD-CE data path**: No

CINST execution resumes with the following instruction in the CINST queue, on the clock cycle after the specified MInst completed.

Typically used to wait for a value to be loaded from HBM into SPAD. Since load times from HBM vary, assembler cannot assume that all `mload`s from MINST queue will complete in order, thus, every `mload` should have a matching `csyncm`.
