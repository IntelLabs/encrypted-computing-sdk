# OpenFHE Tracer

This directory contains the HERACLES tracer implementation for OpenFHE, which enables extraction of FHE computation traces for use with the p-ISA tools.

## Overview

The OpenFHE tracer captures homomorphic encryption operations performed by OpenFHE and generates trace files that can be processed by the p-ISA toolchain. This enables:

- Extraction of FHE instruction sequences
- Generation of data traces for polynomial operations
- End-to-end compilation from FHE programs to hardware accelerator instructions

## Files

- `tracer.h` - Main tracer implementation that hooks into OpenFHE's tracing infrastructure
- `tracing_example.cpp` - Example program demonstrating tracer usage with basic FHE operations
- `CMakeLists.txt` - Build configuration that fetches OpenFHE with tracing support enabled

## Building

From the repository root:

```bash
# Configure the project
mkdir -p build
cmake -B build -S p-isa_tools

# Build the tracing example
cmake --build build --target tracing_example
```

## Running the Example

To run the complete end-to-end tracing pipeline:

```bash
cmake --build build --target run_tracing_example
```

This will:
1. Execute the tracing example, generating trace files in `build/end-to-end-test/`:
   - `tracing_example.bin` - FHE instruction trace
   - `tracing_example_data.bin` - Data trace with polynomial values
2. Run the program mapper on the instruction trace to generate `tracing_example.bin.csv`
   (this internally uses the kernel generator)
3. Run the functional modeler to process the traces (see note below)

### Output Files

After running, you'll find the following in `build/end-to-end-test/`:
- `tracing_example.bin` - Binary FHE instruction trace
- `tracing_example_data.bin` - Binary data trace
- `tracing_example.bin.csv` - Mapped instruction sequence
- `tracing_example_pisa.csv` - p-ISA instructions (if functional modeler succeeds)

## Known Issues

> **Note:** The functional modeler may fail with an error about missing `partQHatInvModq`. This is currently expected as recent versions of OpenFHE no longer use this parameter internally, but the p-isa_tools still expect it.

## Usage in Your Own Code

To use the tracer in your OpenFHE application:

```cpp
#include "tracer.h"

// After creating your CryptoContext
auto cc = GenCryptoContext(parameters);

// Create and attach the tracer
IF_TRACE(auto tracer = std::make_shared<HeraclesTracer<DCRTPoly>>("output_name", cc));
IF_TRACE(cc->setTracer(tracer));

// Your FHE operations will now be traced
auto result = cc->EvalAdd(cipher1, cipher2);

// Save trace files
IF_TRACE(tracer->saveBinaryTrace());
IF_TRACE(tracer->saveJsonTrace()); // for debugging/manual inspection
```

## Dependencies

Note: these are automatically fetched/created by CMake when using `run_tracing_example`

- OpenFHE
- HERACLES_DATA_FORMATS library (built as part of p-isa_tools)
- Python environment with kerngen for program mapping
