# HERACLES Program Mapper

## Table of Contents
1. [Requirements](#requirements)
2. [Build Configuration](#build-configuration)
   1. [Build Type](#build-type)
      1. [Third-Party Components](#third-party-components)
3. [Building](#building)
4. [Running the Program Mapper](#running-the-program-mapper)
5. [Code Formatting](#code-formatting)

## Requirements

Current build system uses `CMake`.

Tested Configuration(s)
- Ubuntu 22.04 (also tested on WSL2)
- C++17
- GCC == 11.3
- CMake >= 3.22.1
- SNAP (used to support graph features)
- JSON for Modern CPP >= 3.11

## Build Configuration

The current build system is minimally configurable but will be improved with
time. The project directory is laid out as follows

- __program_mapper__ *src directory for the program mapper*
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
This backend requires the following third party components:

- [SNAP](https://github.com/snap-stanford/snap.git)
- [JSON for modern c++](https://github.com/nlohmann/json)

These external dependencies are fetched and built at configuration time by
`cmake`, see below how to build the project.

## Building
Build from the top level of p-isa-tools with Cmake as follows:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

Build type can also be changed to `Debug` depending on current needs (Debug
should be used if the tool is being used to actively debug failing kernels).

## Running the Program Mapper

Located in `build/bin` is an executable called **program_mapper**. This program
can be used to generate a graph of combined p-isa instructions with a
supplementary memory file, and a combined p-isa kernel from a program trace.
The program accepts a number of commandline options to control its usage.

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

--straceV0, --st0, -t0 <path_to_seal_v0_trace_file>
 Location of a seal trace file in v0 format

--verbose, -v
 Enables more verbose execution reporting to std out

-h, /h, \h, --help, /help, \help
    Shows this help.
```

## Code Formatting
The repository includes `pre-commit` and `clang-format` hooks to help ensure
code consistency.  It is recommended to install `pre-commit` and `pre-commit
hooks` prior to committing to repo.
