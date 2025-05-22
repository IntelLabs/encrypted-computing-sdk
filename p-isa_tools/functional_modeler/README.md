# HERACLES P-ISA Functional Modeler

## Table of Contents
1. [Requirements](#requirements)
2. [Build Configuration](#build-configuration)
   1. [Build Type](#build-type)
      1. [Third-Party Components](#third--party-components)
3. [Building](#building)
4. [Running the Functional Modeler](#running-the-functional-modeler)
5. [Running the Program Mapper](#running-the-program-mapper)
   1. [Scripts](#scripts)
6. [Code Formatting](#code-formatting)


## P-ISA Documentation
Here is some documentation on the [P-ISA Instruction Set] (@ref PISA_overview)

## Requirements

Current build system uses `CMake`.

Tested Configuration(s)
- Ubuntu 22.04 (also tested on WSL2)
- C++17
- GCC == 11.3
- CMake >= 3.22.1
- SNAP (used to support graph features)
- graphviz (used for graph rendering)
- JSON for Modern CPP >= 3.11

## Build Configuration

The current build system is minimally configurable but will be improved with
time. The project directory is laid out as follows

- __functional_modeler__ *src directory for the functional modeler*
- __common__ *Common code used by p-isa tools*

### Build Options
The Follow options can be specified as cmake defines to enable / disable building of project components
    - ENABLE_DATA_FORMATS="ON"
    - ENABLE_FUNCTIONAL_MODELER="ON"
    - ENABLE_PROGRAM_MAPPER="ON"
    - ENABLE_P_ISA_UTILITIES="ON"

### Build Type

If no build type is specified, the build system will build in <b>Debug</b>
mode. Use `-DCMAKE_BUILD_TYPE` configuration variable to set your preferred
build type:

- `-DCMAKE_BUILD_TYPE=Debug` : debug mode (default if no build type is specified).
- `-DCMAKE_BUILD_TYPE=Release` : release mode. Compiler optimizations for release enabled.
- `-DCMAKE_BUILD_TYPE=RelWithDebInfo` : release mode with debug symbols.
- `-DCMAKE_BUILD_TYPE=MinSizeRel` : release mode optimized for size.

#### Third-Party Components <a name="third-party-components"></a>
This backend requires the following third party components:

- [SNAP](https://github.com/snap-stanford/snap.git)
- [JSON for modern c++](https://github.com/nlohmann/json)

These external dependencies are fetched and built at configuration time by
`cmake`, see below how to build the project.

## Building
Build from the top level of P-ISA-Functional-modeler with Cmake as follows:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Build type can also be changed to `Debug` depending on current needs (Debug
should be used if the tool is being used to actively debug failing kernels).

## Running the Functional Modeler

Once `make` completes the you will find an executable in `build/bin` called
**functional_modeler**.  This program can be used to functionally test p-isa
kernels against a seal trace, render p-isa kernels into a visible graph, and
debug kernel execution.
The program accepts a number of commandline options to control its usage.

A standard test is of the form
```bash
./functional_modeler <he_op.csv> --strace <he_op_trace_v0.json>
```
For example

```bash
functional_modeler p_isa_ops/t.2.add.14.csv --strace traces/add_16384_l2_m3_v0.json
```

performs a functional check for a 16k poly mod add operation checked against a
seal trace containing inputs and outputs.

The full list of currently supported options are listed below.
```bash
Usage:
    functional_modeler p_isa_op OPTIONS

POSITIONAL ARGUMENTS: 1
p_isa_op
 Location of a file containing a list in CSV format for p_isa instructions

OPTIONS:
  --json_data, --json, -jd                            Location of a json data file containing HEC formatted data
  --input_memory_file, --imem, -im                    Location of a memory file to be read and set as input before executing any instructions
  --output_memory_file, --omem, -om                   Location to write a memory file containing all device memory after all instructions have been executed
  --program_inputs_file, --pif, -if                   Location to a file containing program inputs in csv format. Loaded after any memory file(s) and data file but before execution
  --program_outputs_file, --pof, -of                  Location to write a file containing program outputs in csv format. Written after program execution
  --graph_file_name, --gn, -gf                        Sets the name of the file for the output graph image [ default=<p_isa_op_file_prefix>.png ]
  --hardware_model, -hwm                              Available hardware models - (HEC-relaxed-mem,HEC-strict-mem,example)
  --hec_dataformats_data, --hdd, -hd                  Location of HEC data-formats data manifest file
  --hec_dataformats_poly_program_location, --hdp, -pp Location of HEC data-formats poly program file
  --verbose, -v                                       Enables more verbose execution reporting to stdout
  --render_graph, -rg                                 Enables rendering of p_isa graph in PNG and DOT file formats
  --export_inputs, -ei                                Exports program inputs file to the file specified by --program_inputs_file or program_inputs.csv if none specified
  --advanced_performance_analysis, -apa               Enables advanced performance analysis and cycle count prediction
  --verbose_output_checking, -voc                     Enables functional validation of functional execution
  --validate_intermediate_results, -vir               Enables functional validation of intermediates - if --disable_function_validation, this will be automatically set to false
  --enable_advanced_debug_tracing, -dt                Enables advanced debug execution and tracing. Warning: May significantly increase memory usage and reduce performance
  --hec_dataformats_mode, --hdfm, -hm                 Uses hec data-formats execution pipeline
  --disable_graphs, --graphs, -g                      Disables graph building and features
  --disable_functional_execution, --nofunctional      Disable functional execution of instruction stream
  --disable_functional_validation, --novalidate, -nfv Disables functional validation of functional execution

-h, /h, \h, --help, /help, \help
    Shows this help.
```

## Code Formatting
The repository includes `pre-commit` and `clang-format` hooks to help ensure
code consistency.  It is recommended to install `pre-commit` and `pre-commit
hooks` prior to committing to repo.
