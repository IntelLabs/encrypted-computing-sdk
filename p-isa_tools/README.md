# P-ISA Tools

## Table of Contents
1. [Requirements](#requirements)
2. [Build Configuration](#build-configuration)
   1. [Build Type](#build-type)
      1. [Third-Party Components](#third-party-components)
3. [Building](#building)
4. [Running the Program Mapper](#running-the-program-mapper)
5. [Running the Functional Modelere](#running-the-functional-modeler)
6. [Code Formatting](#code-formatting)

## Requirements

Currently, our build system uses `CMake`.

### Currently tested configuration(s)
- Ubuntu 22.04 (also tested on WSL2)
- C++17
- GCC == 11.3.x &emsp; ***This version is a hard requirement at the moment***
- CMake >= 3.22.1
- SNAP (used to support graph features)
- JSON for Modern CPP >= 3.11

## Build Configuration

The current build system is minimally configurable but will be improved with
time. The project directory is laid out as follows

- __program_mapper__ *src directory for the Program mapper*
- __kerngen__ *src directory for the Kernel generator*
- __functional_modeler__ *src directory for the Functional modeler*
- __common__ *Common code used by p-isa tools*

**NOTE:** If using an IDE then it is recommended to set the `INC_HEADERS` flag
to include the header files in the project filesystem. This can be done
via `-DINC_HEADERS=TRUE`.

### Build Type

If no build type is specified, the build system will build in <b>Debug</b>
mode. Use `-DCMAKE_BUILD_TYPE` configuration variable to set your preferred
build type:

- `-DCMAKE_BUILD_TYPE=Debug` : debug mode (default if no build type is specified).
- `-DCMAKE_BUILD_TYPE=Release` : release mode. Compiler optimizations for release enabled.
- `-DCMAKE_BUILD_TYPE=RelWithDebInfo` : release mode with debug symbols.
- `-DCMAKE_BUILD_TYPE=MinSizeRel` : release mode optimized for size.

#### Third-Party Components <a name="third-party-components"></a>
The P-ISA tools require the following third party components:

- [SNAP](https://github.com/snap-stanford/snap.git)
- [JSON for modern c++](https://github.com/nlohmann/json)

These external dependencies are fetched and built at configuration time by
`cmake`, see below how to build the project.

## Building
Always build from the top level of p-isa-tools with Cmake as follows:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Build type can also be changed to `Debug` depending on current needs (Debug
should be used if the tool is being used to actively debug failing kernels).

**NOTE:** Once the build completes, you will find the ***program_mapper*** and
the ***functional_modeler*** executables in `build/bin` directory.

## Running the Program Mapper

The ***program_mapper*** is used to generate a graph of combined p-isa instructions
with a supplementary memory file, and a combined p-isa kernel from a program
trace. The program accepts a number of commandline options to control its usage.

A typical run is of the form
```bash
program_mapper <program_trace.csv> <path-to-kerngen.py>
```

The standard list of currently supported options are listed below.
```bash
Usage:
    program_mapper program_trace kerngen_loc OPTIONS

POSITIONAL ARGUMENTS: 2
program_trace
 Location of a file containing a list in csv format for p_isa instructions

kerngen_loc
 Location of the kerngen.py file

OPTIONS:
--cache_dir, --cache, -c <name of the kernel cache directory>
 Sets the name of the kernel cache directory [Default: ./kernel_cache]

--disable_cache, --no_cache, -dc
 Disables the use of a cache for Ninja kernels

--disable_graphs, --graphs, -g
 Disables graph building and features

--disable_namespace, --nns, -n
 Disables applying register name spacing on PISAKernel nodes

--dot_file_name, -df <name of the dot file to output>
 Sets the name of the output dot file

--enable_memory_bank_output, --banks, -b
 Will output P-ISA programs with registers that include hard coded memory banks when enabled

--export_dot, -ed
 Export seal trace and p_isa graphs to dot file format

--out_dir, --out, -o <name of the output directory>
 Sets the location for all output files [Default: ./]

--remove_cache, --rm_cache, -rc
 Remove the kernel cache directory at the end of the program

--verbose, -v
 Enables more verbose execution reporting to std out

-h, /h, \h, --help, /help, \help
    Shows this help.
```

## Running the Functional Modeler

The ***functional_modeler*** is used to functionally test p-isa kernels
against a data trace (currently only obtained by tracing the excution of
the MS-SEAL library) and debug kernel execution. In addition, the
***functional_modeler*** can also generate a graph of the p-isa kernels,
render such graphs into a visible graph, and estimates the perfomance of
such kernels based on configurable HW models.

The program accepts a number of commandline options to control its usage.

A typical run is of the form
```bash
./functional_modeler <he_op.csv> --strace <he_op_trace_v0.json>
```

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
