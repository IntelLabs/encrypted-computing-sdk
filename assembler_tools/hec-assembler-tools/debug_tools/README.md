# Debug Tools

This folder contains a collection of scripts designed to assist with debugging and testing various aspects of the assembler and instruction scheduling processes.

## Dependencies <a name="dependencies"></a>

These tools are Python based. Dependencies for these scripts are the same as [those](../README.md#dependencies) for the parent project.

> **Note**:  Ensure the `assembler` folder is included in your Python `PATH`.
> ```bash
> export PYTHONPATH="${PYTHONPATH}:$(pwd)/assembler"
> ```

Below is a detailed description and usage example for each tool.

---

## Tools Overview

### `main.py`

  This script serves as the main entry point for running ASM-ISA assembly and P-ISA scheduling processes. It handles the preprocessing, assembly, and scheduling of instructions, transforming them from high-level representations to executable formats.

  The script is used to convert P-ISA kernels into ASM-ISA instructions, manage memory models, and ensure that instructions are scheduled correctly according to dependencies and resource constraints.

- **Usage**:
  ```bash
  python main.py --mem_file <memory_file> --prefix <input_prefix> --isa_spec <isa_spec_file> -v
  ```
  - `--mem_file`: Specifies the input memory file.  
  - `--prefix`: One or more input prefixes to process, representing different instructions or kernels.  
  - `--isa_spec`: Input ISA specification (.json) file that defines the parameters of the instruction set architecture.  
  - `-v`: Enables verbose mode.

---

### `isolation_test.py`

  This script isolates specific variables in P-ISA by replacing instructions that do not affect the specified variables with NOPs (no operation instructions). The isolation test is used to focus on specific variables within a P-ISA kernel, allowing developers to analyze the impact of these variables.

- **Usage**:
  ```bash
  python isolation_test.py --pisa_file <pisa_file> --xinst_file <xinst_file> --out_file <output_file> --track <variables_to_track> -v
  ```
  - `--pisa_file`: Input P-ISA prep (.csv) file containing instructions.  
  - `--xinst_file`: Input XInst instruction file.  
  - `--out_file`: Output file name where the modified instructions will be saved.  
  - `--track`: Set of variables to track.  
  - `-v`: Enables verbose mode.

---

### `deadlock_test.py`

  This script checks for deadlocks in the CInstQ and MInstQ caused by sync instructions. It raises an exception if a deadlock is found, indicating a potential issue in instruction scheduling.

- **Usage**:
  ```bash
  python deadlock_test.py <input_dir> [input_prefix]
  ```
  - `<input_dir>`: Directory containing instruction files, typically organized by prefixes.  
  - `[input_prefix]`: Optional prefix for instruction files, used to specify particular sets of instructions.

---

### `order_test.py`
  This script tests all registers in an XInstQ to determine if any register is used out of order based on the P-ISA instruction order. It is specifically designed for kernels that do not involve evictions.

  The script helps ensure that registers are accessed in the correct sequence, which is crucial for maintaining the integrity of instruction execution in systems where register order matters. This is particularly important for debugging and optimizing instruction scheduling.

- **Usage**:
  ```bash
  python order_test.py --input_file <xinst_file> -v
  ```
  - `--input_file`: Specifies the input (.xinst) file containing the XInstQ instructions.
  - `-v`: Enables verbose mode for detailed output, providing insights into the processing steps and results.

### `xinst_timing_check/inject_bundles.py`

  This script injects dummy bundles into instruction files after the first bundle, simulating additional instruction loads for testing purposes. The injection of dummy bundles is used to test the system's handling of instruction loads and synchronization points.

- **Usage**:
  ```bash
  python inject_bundles.py <input_dir> <output_dir> [input_prefix] [output_prefix] --isa_spec <isa_spec_file> -b <dummy_bundles> -ne
  ```
  - `<input_dir>`: Directory containing input files to be processed.  
  - `<output_dir>`: Directory to save output files with injected bundles.  
  - `[input_prefix]`: Optional prefix for input files, specifying the target instruction set.  
  - `[output_prefix]`: Optional prefix for output files, defining the naming convention for saved files.  
  - `--isa_spec`: Input ISA specification (.json) file, providing architectural details.  
  - `-b`: Number of dummy bundles to insert, simulating additional instruction loads.  
  - `-ne`: Skip exit in dummy bundles, altering the behavior of injected instructions.

---

### `xinst_timing_check/xtiming_check.py`

  This script checks timing for register access, ensuring registers are not read before their write completes, and checks for bank write conflicts.

- **Usage**:
  ```bash
  python xtiming_check.py <input_dir> [input_prefix] --isa_spec <isa_spec_file>
  ```
  - `<input_dir>`: Directory containing input files for timing analysis.  
  - `[input_prefix]`: Optional prefix for input files, specifying the target instruction set.  
  - `--isa_spec`: Input ISA specification (.json) file, providing architectural details for timing validation.

---
