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

Note: Python ```protobuf==4.23.0``` module is required to run the Python test. It can be installed via
```bash
pip install -r requirements.txt
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

### Importing the **HERACLES-Data-Formats** Library

For Python protobuf to work, first the Python ```protobuf``` module is required. It can be installed via
```bash
pip install -r requirements.txt
# or
pip install protobuf==4.23.4
```

The ```PYTHONPATH``` environment variable needs to be set to point to the protobuf generated files:
```bash
export PYTHONPATH=${HERACLES_DATA_FORMATS_DIR}/python/:${PYTHONPATH}
```
(with `HERACLES_DATA_FORMATS_DIR` as defined above for building
dependent C++ projects and/or pointing to the install location in case
you installed this project).

### Usage example
The **HERACLES-Data-Formats** library can be imported via, e.g.,
```python
from heracles.proto.common_pb2 import Scheme
from heracles.proto.fhe_trace_pb2 import Trace, Instruction
```
Refer to the [heracles_test.py](src/data_formats/test/heracles_test.py) script for
examples of using Heracles protobuf objects and utility functions as
well as [Protocol Buffer Basics:
Python](https://protobuf.dev/getting-started/pythontutorial/) for more
general information on using generated python protobuf code.
