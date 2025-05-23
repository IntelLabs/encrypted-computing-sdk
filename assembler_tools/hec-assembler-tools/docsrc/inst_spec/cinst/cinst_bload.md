# BLOAD - CInst {#bload_CInst}

Load metadata from scratchpad to register file.

## Definition

Loads metadata from scratchpad to special registers in register file.

| instr | operand 0 | operand 1 | operand 2 |
|-|-|-|-|
| bload | meta_target_idx | spad_src | src_col_num |

## Timing

**Throughput**: 1 clock cycle

**Latency**: 1 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `meta_target_idx` | int32 | Metadata register index in the range `[0, 32)`. |
| `spad_src` | spad_addr | SPAD address of metadata variable to load. |
| `src_col_num` | int32 | Block number inside metadata source variable in the range `[0, 4)` (see notes). |

### Notes

**Uses SPAD-CE data path**: Yes

Some operations require metadata to indicate parameters and modes of operation that don't change throughout the execution of a program. Metadata is usually loaded once at the start of the program into special registers in the CE.

The main use of this type of metadata is to generate twiddle factors.

The destination registers for this instruction are special metadata registers of size 1/4 word. Each is indexed by parameter `meta_target_idx`.

The source metadata to load is a word in SPAD addressed by `spad_src`. It needs to be partitioned into 4 blocks of size 1/4 word each to fit into the target registers. Since the smallest addressable unit is the word, `bload` features the parameter `src_col_num` to address the block inside the word as shown in the diagram below.

```
word  [--------------------------]
block [--0--][--1--][--2--][--3--]
```

Metadata sources must be loaded into the destination registers in the order they appear. If there are `N` metadata variables to load, metadata target index, `meta_target_idx`, monotonically increases with every `bload` from `0` to `4 * N - 1 < 32`.

There are only 32 destination registers in the CE, supporting up to 8 words of metadata. If there are more words of metadata, then metadata needs to be swapped as needed, requiring tracking of which metadata is loaded for twiddle factor generation.
