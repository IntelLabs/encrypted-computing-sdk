cmake_minimum_required(VERSION 3.15.0...3.24.0)

project(HERACLES_DATA_FORMATS VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(HERACLES_DATA_FORMATS_CMAKE_PATH "${CMAKE_CURRENT_LIST_DIR}/cmake")
include(CMakePackageConfigHelpers)
include(GNUInstallDirs)

# Set default output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_BINDIR}")

include(${PROJECT_SOURCE_DIR}/cmake/utils.cmake)
include(${PROJECT_SOURCE_DIR}/cmake/protobuf.cmake)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -O3 -fPIC")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -O3 -fPIC")
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
set(CMAKE_INSTALL_RPATH "$ORIGIN;$ORIGIN/${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_INSTALL_LIBDIR})

find_package(OpenMP REQUIRED)

option(BUILD_TEST "Build c++/python tests with ctest" ON)
enable_testing()

add_subdirectory(proto)
add_subdirectory(cpp)
if(BUILD_TEST)
  add_subdirectory(test)
endif()

# install python utility functions
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/python/
  DESTINATION python
  # TODO(skmono): to be added afterwards
  # FILES_MATCHING
  # PATTERN "*.py"
)

# copy python utility functions to build/python
add_custom_target(HERACLES_DATA_FORMATS_COPY_PYTHON
  ALL
  DEPENDS HERACLES_data_proto
)
add_custom_command(
  TARGET HERACLES_DATA_FORMATS_COPY_PYTHON
  POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_CURRENT_LIST_DIR}/python ${PROJECT_BINARY_DIR}/python/
)

option(ENABLE_OPENFHE_TRACER "Build the OpenFHE tracer" ON)
if(ENABLE_OPENFHE_TRACER)
add_subdirectory(tracers/openfhe)
endif()
