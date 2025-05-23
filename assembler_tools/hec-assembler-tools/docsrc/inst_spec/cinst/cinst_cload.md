# CLOAD - CInst {#cload_CInst}

Load a single polynomial residue from scratchpad into a register.

## Definition

Load a word, corresponding to a single polynomial residue, from scratchpad memory into the register file memory.

| instr | operand 0 | operand 1 |
|-|-|-|
| cload | dst | src |

## Timing

**Throughput**: 4 clock cycles

**Latency**: 4 clock cycles

## Details

| Operand | Type | Description |
|-|-|-|
| `dst` | register | Destination register where to load the word. |
| `src` | spad_addr | SPAD address from where to load. |

### Notes

**Uses SPAD-CE data path**: Yes

The register is ready to be used on the clock cycle after `cload` completes. Using the register during `cload` is undefined.

Instruction `cload` writes to CE registers and thus, it can conflict with another XInst if both are writing to the same bank and get scheduled such that their write phases happen on the same cycle. Because the rule that there cannot be more than one write to the same bank in the same cycle this conflict must be avoided.

Two ways to mitigate the above conflict are:

- Carefully track and sync `cload` instructions with all XInsts.
- Use a convention such that `cload` instructions always write to one bank while all other XInsts cannot write their outputs to that bank.

We have adopted the second option to implement the assembler. First option is cumbersome and prone to errors: By convention, `cload` should always load into **bank 0**. No XInst can write outputs to **bank 0**.
