# HCGF Instruction Specification {#HCGF_specs}

Terms used in this document are defined in the HERACLES Instruction Set Architecture (ISA).

[Changelog](changelog.md)

## Table of Contents
1. [Introduction](#introduction)
2. [Memory Specification](#mem_spec)
   1. [Word Size](#word_spec)
   2. [High-Bandwidth Memory (HBM)](#hbm_spec)
   3. [Scratch Pad (SPAD)](#spad_spec)
   4. [Register Banks](#registers_spec)
3. [Output File Formats](#output_format)
   1. [XINST File](#output_xinst)
   2. [CINST File](#output_cinst)
   3. [MINST File](#output_minst)
4. [Instruction Set](#instr_spec)

## Introduction <a name="introduction"></a>

HERACLES architecture allows fine-grained control of memory movement between DRAM, SRAM, and register files. The architecture features three execution queues that control memory movement among the different levels, as well as control of the compute engine.

The three execution queues are:

- XINST: contains the Compute Engine (CE) instructions (XInst) to be loaded into the instruction queue of tiles to carry out computations.

  **Queue Capacity**: 1MB.

  **Instruction size**: 64 bits.

- CINST: contains the instructions (CInst) to coordinate memory movement between the register banks in the CE and the SRAM cache (also known as scratch pad, or SPAD).

  **Queue Capacity**: 128KB.

  **Instruction size**: 64 bits.

- MINST: contains the instructions (MInst) to coordinate memory movement between the SPAD and DRAM (also known as high-bandwidth memory, or HBM).

  **Queue Capacity**: 128KB.

  **Instruction size**: 64 bits.

The three queues must work in concert to ensure memory consistency and optimized, functional correctness of the execution.

The output of the assembler tool is composed of three files containing the instructions for each of the three execution queues for the HERACLES respectively.

## Memory Specification <a name="mem_spec"></a>

#### Summary of Sizes and Memory Capacities in HERACLES Instructions and Memory Model

| Parameter | Size | Unit | Word size | Description |
|-|-|-|-|-|
| Word size | 32 | KB | 1 | Data unit size. |
| XINST Queue Capacity | 1 | MB | 512 | Capacity of XInst queue in Cfetch engine. |
| CINST Queue Capacity | 128 | KB | 4 | Capacity of CInst queue in Cfetch engine. |
| MINST Queue Capacity | 128 | KB | 4 | Capacity of MInst queue in Mfetch engine. |
| XINST Intruction width | 64 | bits | | Size of instructions in the Xinst queue. |
| CINST Intruction width | 64 | bits | | Size of instructions in the Cinst queue. |
| MINST Intruction width | 64 | bits | | Size of instructions in the Minst queue. |
| XINST bundle size | 64 | instructions | | Number of instructions in an XInst bundle. |
| HBM Capacity`*` | 48 | GB | 1,572,864 | Capacity of DRAM. |
| SPAD Capacity`*` | 48 | MB | 1,536 | Capacity of SRAM/cache. |
| Store Buffer capacity | 128 | KB | 4 | Capacity of the intermediate data buffer queue for `xstore`. |
| Register banks | 4 | banks | | Number of register banks in a compute tile pair. |
| Registers per bank | 72 | registers | | Number of registers in a register bank. |
| Register capacity | 32 | KB | 1 | Capacity of a combined register for all compute tile pairs. |

`*`Capacities configurable during assembling.

See HERACLES ISA for more information.

### Word Size <a name="word_spec_"></a>

A "word" is the *smallest addressable data unit* in the HERACLES memory model.

**Word size**: 32KB.

HERACLES is a polynomial computation engine, and thus, a word contains the coefficients for a polynomial.

**Polynomial coefficient size**: 4B or 32bits.

A word has capacity to hold polynomials of, up to, 8192 coefficients.

Operations on larger polynomials is possible by splitting them into equivalent mathematical operations on smaller polynomials.

Data sizes in bytes are offered for *reference purposes only*. Since the smallest addressable unit is the word, **all HERACLES instructions are word-based**.

Note that the information included here is at the abstraction level that concerns the assembler. The HERACLES architecture further partitions the memory into blocks, and the compute engine into 64 compute tile pairs. For more information on the low level architecture refer to the HERACLES architecture documentation.

### High-Bandwidth Memory (HBM) <a name="hbm_spec"></a>

**HBM capacity**: 48GB == 1,572,864 words.

HBM is partitioned into four regions:

- Data region
- XInst region
- CInst region
- MInst region

Each memory region will contain the namesake data for the whole HERACLES program. Their size is custom defined (in words) by the host during initialization through the driver. Their total size must add up to the total capacity of the HBM.

While all the regions live in HBM space, their logical base address is always `0`. This means that, for example, the address `p` from the data region is in a different location of HBM than the address `p` from the XInst region. The definition of instructions that access HBM will specify which region they access.

During HERACLES initialization, the host will copy the program parts into the corresponding memory regions. Once the transfer is complete, the host signals HERACLES through the driver to start the program.

When the program starts, a state machine in the hardware will start streaming the contents of MInst and CInst memory regions into their corresponding queues in 64KB chunks. Note that these queues have a capacity of 128KB each, thus, the streaming will occur into the upper or lower 64KB portion not currently being executed, overwriting code already executed.

Instruction pointers for MINST and CINST queues will automatically start once there is code ready to execute. The hardware state machine will ensure that there is always code ready for execution.

Execution of XINST queue, however is controlled by CInst.

### Scratch Pad (SPAD)  <a name="spad_spec"></a>

**SPAD capacity**: 48MB == 1,536 words.

Data transfers from CE into SPAD are initiated by XINST via `xstore` instruction. The data is temporarily pushed into an intermediate data buffer queue. It is the CINST's responsibility to pop this intermediate queue and complete the transfer into SPAD before the buffer overflows.

Data transfers from SPAD into the CE's register file are available in the corresponding registers one clock cycle after the transfer instruction completes.

#### SPAD Restrictions

- There cannot be multiple operations that use the data path between SPAD and CE in flight.

**Temporary Store Queue Buffer capacity**: 4 words.

### Register Banks <a name="registers_spec"></a>

The CE features 64 compute tile pairs (these are the compute units of the CE) arranged in 8 rows of 8 tile pairs. Each tile pair has 4 register banks with 72 registers. Each register has a capacity of 512 bytes. However, the architecture will ensure that all tile pairs will execute the same instruction on the same clock cycle on the same registers; therefore, we can treat the CE as a unit with the characteristics listed below.

As a unit, the CE features a register file with 4 **register banks**.

**Registers per bank**: 72.

**Register capacity**: 1 word.

#### Bank Restrictions

- A register bank cannot be accessed for reading more than once in the same cycle. Reads normally occur on the first cycle of instructions.

- A register bank cannot be accessed for writing more than once in the same cycle. Writes normally occur on the last cycle of instructions.

- A register bank can be accessed for a single read and a single write simulataneously in the same cycle.

## Output File Formats <a name="output_format"></a>

The assembler provides its output in three csv-style files.

#### Comments

All output files support inline comments using the hash symbol `#`. All text to the right of a `#` in a line is ignored as a comment.

Note that full line comments are not supported, and every line must contain an instruction.

### XINST File <a name="output_xinst"></a>

Contains the instructions for the XINST execution queue.

File extension: `.xinst`

File format:

```csv
F<bundle_num>, <trace_instr_num>, <op>, <dests>, <sources>, <other>, <residual>
```

| Field | Type | Description |
|-|-|-|
| `bundle_num` | int32 | ID of bundle to which this instruction belongs. Instructions are grouped by bundles, so, this value is never smaller than previous instructions. |
| `trace_instr_num` | int32 | Matching input kernel instruction that caused the generation of this instruction. For book keeping purposes. |
| `op` | string | Name of the instruction. |
| `dests` | csv_string | Comma-separated list of all destinations for the instruction. 0 or more values. |
| `sources` | csv_string | Comma-separated list of all sources for the instruction. 0 or more values. |
| `other` | csv_string | Comma-separated list of any extra parameters required for the operation that are not specifically listed here. 0 or more values. |
| `residual` | int32 | Residual for the operation. |

Note that some of the elements after the instruction name may be missing, depending on the instruction.

Example:

```csv
F99, 1056, ntt, r24b2, r25b3, r60b2, r61b3, r35b1, 13, 12 # dst: r24b2, r25b3, src: r60b2, r61b3, r35b1, stage: 13, res: 12
```

Check instruction specification for exceptions.

### CINST File <a name="output_cinst"></a>

Contains the instructions for the CINST execution queue.

File extension: `.cinst`

File format:

```csv
<instr_num>, <op>, <dests>, <sources>, <other>
```

| Field | Type | Description |
|-|-|-|
| `instr_num` | int32 | Monotonically increasing instruction number. |
| `op` | string | Name of the instruction. |
| `dests` | csv_string | Comma-separated list of all destinations for the instruction. 0 or more values. |
| `sources` | csv_string | Comma-separated list of all sources for the instruction. 0 or more values. |
| `other` | csv_string | Comma-separated list of any extra parameters required for the operation that are not specifically listed here. 0 or more values. |

Note that some of these elements after the instruction name may be missing, depending on the instruction.

Example:

```csv
55, cload, r60b0, 9 # dst: r60b0, src: 9
```

Check instruction specification for exceptions.

### MINST File <a name="output_minst"></a>

Contains the instructions for the MINST execution queue.

File extension: `.minst`

File format:

```csv
<instr_num>, <op>, <dests>, <sources>, <other>
```

| Field | Type | Description |
|-|-|-|
| `instr_num` | int32 | Monotonically increasing instruction number. |
| `op` | string | Name of the instruction. |
| `dests` | csv_string | Comma-separated list of all destinations for the instruction. 0 or more values. |
| `sources` | csv_string | Comma-separated list of all sources for the instruction. 0 or more values. |
| `other` | csv_string | Comma-separated list of any extra parameters required for the operation that are not specifically listed here. 0 or more values. |

Note that some of these elements after the instruction name may be missing, depending on the instruction.

Example:

```csv
54, mload, 40, 29 # dst: 40, src: 29
```

Check instruction specification for exceptions.

## Instruction Set <a name="instr_spec"></a>

Instructions are pipelined. Thus, they will have a throughput time and a total latency.

Throughput time is the number of clock cycles that it takes for the instruction to be dispatched. The execution engine will not move to the next instruction in the queue until the throughput time for the current instruction has elapsed. Most instructions have a throughput time of 1 clock cycle.

Latency is the number of clock cycles it takes for the instruction to complete and its outputs to be ready. It includes the throughput time. Most Xinst have a latency of 6 clock cycles. See the instruction specification for details and exceptions.

Because of pipelining, there can be several instructions in flight at the same time. The code produced by the assembler ensures that dependent instructions don't read or write data before their dependency has resolved, this is, until the previous instruction's latency has elapsed.

The following instruction set functionally matches those of HERACLES ISA. It is provided here as a reference for syntax and semantics of the output generated by the HCGF assembler.

#### Instructions - Assembler Output

| MINST | CINST | XINST |
|-|-|-|
| [msyncc](inst_spec/minst/minst_msyncc.md) | [bload](inst_spec/cinst/cinst_bload.md) | [move](inst_spec/xinst/xinst_move.md) |
| [mload](inst_spec/minst/minst_mload.md) | [bones](inst_spec/cinst/cinst_bones.md) | [xstore](inst_spec/xinst/xinst_xstore.md) |
| [mstore](inst_spec/minst/minst_mstore.md) | [nload](inst_spec/cinst/cinst_nload.md) | [rshuffle](inst_spec/xinst/xinst_rshuffle.md) |
|  | [xinstfetch](inst_spec/cinst/cinst_xinstfetch.md) | [ntt](inst_spec/xinst/xinst_ntt.md) |
|  | [ifetch](inst_spec/cinst/cinst_ifetch.md) | [twntt](inst_spec/xinst/xinst_twntt.md) |
|  | [cload](inst_spec/cinst/cinst_cload.md) | [twintt](inst_spec/xinst/xinst_twintt.md) |
|  | [cstore](inst_spec/cinst/cinst_cstore.md) | [intt](inst_spec/xinst/xinst_intt.md) |
|  | [csyncm](inst_spec/cinst/cinst_csyncm.md) | [add](inst_spec/xinst/xinst_add.md) |
|  | [cexit](inst_spec/cinst/cinst_cexit.md) | [sub](inst_spec/xinst/xinst_sub.md) |
|  | [nop](inst_spec/cinst/cinst_nop.md) | [mul](inst_spec/xinst/xinst_mul.md) |
|  |  | [muli](inst_spec/xinst/xinst_muli.md) |
|  |  | [mac](inst_spec/xinst/xinst_mac.md) |
|  |  | [maci](inst_spec/xinst/xinst_maci.md) |
|  |  | [exit](inst_spec/xinst/xinst_exit.md) |
|  |  | [nop](inst_spec/xinst/xinst_nop.md) |
