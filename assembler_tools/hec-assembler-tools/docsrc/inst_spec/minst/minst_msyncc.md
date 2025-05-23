# MSYNCC - MInst {#msyncc_MInst}

MINST execution waits for a particular instruction in CINST queue to complete.

## Definition

Wait instruction similar to a barrier that stalls the execution of MINST queue until the specified instruction from CINST queue has completed.

| instr | operand 0 |
|-|-|
| msyncc | inst_num |

## Timing

**Throughput**: varies

**Latency**: Same as throughput.

## Details

| Operand | Type | Description |
|-|-|-|
| `inst_num` | int32 | Instruction number from the QINST queue for which to wait. |

### Notes

MINST execution resumes with the following instruction in the MINST queue, on the clock cycle after the specified CInst completed.

Typically used to wait for a value cached in SPAD to be updated before storing it into HMB.
