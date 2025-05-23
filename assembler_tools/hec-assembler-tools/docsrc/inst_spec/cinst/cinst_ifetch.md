# IFETCH - CInst {#ifetch_CInst}

Fetch a bundle of instructions for execution.

## Definition

Fetch a bundle of instructions from the XINST queue and send it to the CE for execution.

| instr | operand 0 |
|-|-|
| ifetch | bundle_idx |

## Timing

**Throughput**: 1 clock cycles `*`

`*` This instruction has the ability to block execution of CINST queue. See details.

**Latency**: 5 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `bundle_idx` | int32 | Index for the bundle of instructions to fetch. The bundle must exist in the current XINST queue. |

### Notes

**Uses SPAD-CE data path**: Yes

A bundle is a collection of a pre-defined number contiguous instructions. The instructions in the bundle must have a minimum throughput of 64 clock cycles (except when there is an `exit` instruction in the bundle). The bundle index to which an instruction belongs is clearly indicated in the encoding of the instruction output by the assembler.

XINST queue contains the instructions for the CE. This queue contains more than one bundle at a time. Instruction `ifetch` schedules the next bundle (from those bundles in XINST) to execute into the CE.

It takes `ifetch` 2 cycles to start, and 4 more cycles before the CE is completely loaded with the entry point to the new bundle.

The loaded bundle starts execution in the clock cycle after `ifetch` completed.

Calling another `ifetch` while a bundle is executing causes undefined behavior. Thus, a new bundle should be fetched after the last bundle's latency elapses.

Note that this instruction uses the SPAD-CE data path, so, code produced must ensure that an `ifetch` is not executed when a XInst `xstore` is in flight from the current bundle in-flight. This can be mitigated by a matching `cstore` before `ifetch`.

`*` XINST queue content is filled out by instruction [`xinstfetch`](cinst_xinstfetch.md) . Instruction `xinstfetch` has a variable latency, and there may be occasions when an `ifetch` is encountered while the referenced bundle is part of code still being loaded by `xinstfetch`. If this is the case, `ifetch` will block until the bundle is ready.
