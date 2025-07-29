# HERACLES Data formatter interface

## CMake Configure and Build
```bash
cmake -S . -B build
cmake --build build --parallel
```
_Note: for now cmake will _not build with `ninja`_ and is only tested for
(default) `CMAKE_GENERATOR='Unix Makefiles`_


## Run test
```bash
cmake --build build --target test
```

Note: Python `[dev]` dependencies from the root `pyproject.toml` are required to run the Python test. They can be installed via
```bash
pip install -e ".[dev]"  # from repository root
```

## C++

### Importing the **HERACLES-Data-Formats** Library

The C++ library be found and included with cmake by including
following statements in the cmakefile of the project depending on the
HERACLES data formats library:
```cmake
find_package(HERACLES_DATA_FORMATS 1.0.0 REQUIRED)
...
target_link_libraries(<YOUR_LIBRARY> PUBLIC HERACLES_DATA_FORMATS::heracles_data_formats)
```
Assuming you follow the convention of having all code
checked out in the same directory and named by their component name, you
can then build that project by executing the following:

```bash
# from project root
HERACLES_DATA_FORMATS_DIR=$(pwd)/../HERACLES-data-formats/build cmake -S . -B build
cmake --build build --parallel
```
Alternatively, you can also build and install HERACLES-data-formats
(with the destination chosen, e.g., using the
`-DCMAKE_INSTALL_PREFIX=/path/to/install` argument, and an `cmake
--build build --target install` after the build ).  However,  when
installing be careful in not forgetting to re-install
after each change and subsequent build or accidentally picking up
older versions installed elsewhere and earlier searched in CMAKE's
search paths.


### Usage example
The library can be used in the ```C++``` code, e.g., as followed:
```c++
// protobuf headers
#include "heracles/heracles_proto.h"
// cpp utility headers
#include "heracles/heracles_data_formats.h"

int main() {
  heracles::fhe_trace::Trace trace;
  heracles::data::InputPolynomials input_polys;

  return 0;
}
```
Refer to the [heracles_test.cpp](src/data_formats/test/heracles_test.cpp) source
code for additional examples of using Heracles protobuf objects and
utility functions as well as [Protocol Buffer Basics:
C++](https://protobuf.dev/getting-started/cpptutorial/) for more
general information on using generated C++ protobuf code.


## Python


For the Python package to be used independently of CMake/C++ builds, the optional `dev` dependencies are required.

1. **Install dependencies**:
```bash
# For development (includes grpcio-tools for compiling protos, pytest for testing)
pip install -e ".[dev]"
```

2. **Compile Protocol Buffers**:
```bash
python p-isa_tools/data_formats/compile_protos.py
```

This generates the Python protobuf files in `p-isa_tools/data_formats/python/heracles/proto/`.

3. **Generate test traces** (if needed for testing):
```bash
python p-isa_tools/data_formats/test/generate_test_traces.py
```
Alternatively, you can simply run the `pytest` tests, which will create the protobuf files and/or test traces if they do not exist yet.

### Running Tests

From the repository root:
```bash
pytest p-isa_tools/data_formats/test/
```
(The path is optional, but avoids running unrelated tests)

### Usage example
The **HERACLES-Data-Formats** library can be imported via, e.g.,
```python
from heracles.proto.common_pb2 import Scheme
from heracles.proto.fhe_trace_pb2 import Trace, Instruction
import heracles.fhe_trace.io as hfi
import heracles.data.io as hdi

# Create and save a trace
trace = Trace()
trace.scheme = Scheme.SCHEME_BGV
hfi.store_trace("my_trace.bin", trace)

# Load a trace
loaded_trace = hfi.load_trace("my_trace.bin")
```

Refer to the [heracles_test.py](test/heracles_test.py) script for
examples of using Heracles protobuf objects and utility functions as
well as [Protocol Buffer Basics:
Python](https://protobuf.dev/getting-started/pythontutorial/) for more
general information on using generated python protobuf code.
