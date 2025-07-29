set(HERACLES_OUTPUT_DIR ${PROJECT_BINARY_DIR}/heracles)
set(HERACLES_PROTO_OUTPUT_DIR ${HERACLES_OUTPUT_DIR}/proto)
set(HERACLES_PYTHON_PROTO_OUTPUT_DIR ${PROJECT_BINARY_DIR}/python/heracles/proto)

file(MAKE_DIRECTORY ${HERACLES_PROTO_OUTPUT_DIR})
file(MAKE_DIRECTORY ${HERACLES_PYTHON_PROTO_OUTPUT_DIR})

# amalgamated single header for protobuf generated files
configure_file(heracles_proto.h.in ${HERACLES_OUTPUT_DIR}/heracles_proto.h)

########
# Build HERACLES_data_proto
########
add_library(HERACLES_data_proto
  OBJECT
  heracles/common.proto
  heracles/maps.proto
  heracles/fhe_trace.proto
  heracles/data.proto
)

target_include_directories(HERACLES_data_proto
  PUBLIC
  $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}>
  $<BUILD_INTERFACE:${HERACLES_PROTO_OUTPUT_DIR}>
  $<INSTALL_INTERFACE:include>
  ${protobuf_INCLUDE_DIR}
)

# include custom protobuf-generate function
include(${PROJECT_SOURCE_DIR}/cmake/protobuf-generate.cmake)

protobuf_generate(
  TARGET HERACLES_data_proto
  LANGUAGE cpp
  IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/heracles ${protobuf_SOURCE_DIR}/src
  PROTOC_OUT_DIR ${HERACLES_PROTO_OUTPUT_DIR}
)

# generate python protobuf library
protobuf_generate(
  TARGET HERACLES_data_proto
  LANGUAGE python
  IMPORT_DIRS ${CMAKE_CURRENT_SOURCE_DIR}/heracles ${protobuf_SOURCE_DIR}/src
  PROTOC_OUT_DIR ${HERACLES_PYTHON_PROTO_OUTPUT_DIR}
)

# patch generated Python protobuf files to support "relative" paths for modules
# this allows using the generated protobuf python files to be correctly imported
add_custom_target(HERACLES_DATA_PROTO_PATCH
  ALL
  DEPENDS
    ${HERACLES_PYTHON_PROTO_OUTPUT_DIR}/fhe_trace_pb2.py
    ${HERACLES_PYTHON_PROTO_OUTPUT_DIR}/data_pb2.py
)

# BSD sed requires space between -i ''
if(APPLE)
  set(sed_space " ")
endif()

# replaces "import common_pb2" to "from . import common_pb2"
add_custom_command(
  TARGET HERACLES_DATA_PROTO_PATCH
  POST_BUILD
  COMMAND sed -i${sed_space}'' '/^import common_pb2 as/s/^/from . /' *_pb2.py
  WORKING_DIRECTORY ${HERACLES_PYTHON_PROTO_OUTPUT_DIR}
)

# install generated protobuf headers
install(DIRECTORY ${HERACLES_OUTPUT_DIR}/
  DESTINATION include/heracles
  FILES_MATCHING
  PATTERN "*.h"
)

# install generated python protobuf files
install(DIRECTORY ${HERACLES_PYTHON_PROTO_OUTPUT_DIR}/
  DESTINATION python/heracles/proto
  FILES_MATCHING
  PATTERN "*.py"
)

# main library build
add_library(heracles_data_formats
  SHARED
  ${HERACLES_PROTO_OUTPUT_DIR}/common.pb.cc
  ${HERACLES_PROTO_OUTPUT_DIR}/data.pb.cc
  ${HERACLES_PROTO_OUTPUT_DIR}/maps.pb.cc
  ${HERACLES_PROTO_OUTPUT_DIR}/fhe_trace.pb.cc
)
add_library(HERACLES_DATA_FORMATS::heracles_data_formats ALIAS heracles_data_formats)

set_target_properties(heracles_data_formats PROPERTIES
  BUILD_WITH_INSTALL_RPATH FALSE
  LINK_FLAGS "-Wl,-rpath,'$ORIGIN'"
)

target_include_directories(heracles_data_formats
  PUBLIC $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}>
  PUBLIC $<BUILD_INTERFACE:${HERACLES_PROTO_OUTPUT_DIR}>
  PUBLIC $<BUILD_INTERFACE:${protobuf_INCLUDE_DIR}>
  PUBLIC $<INSTALL_INTERFACE:include>
)

# Required for linking protobuf library
target_link_directories(heracles_data_formats
  PUBLIC $<BUILD_INTERFACE:${protobuf_LIB_DIR}>
  PUBLIC $<INSTALL_INTERFACE:lib>
)

find_package(ZLIB REQUIRED)
target_link_libraries(heracles_data_formats PRIVATE ZLIB::ZLIB)
if(UNIX AND NOT APPLE)
  target_link_libraries(heracles_data_formats PRIVATE rt)
endif()

add_dependencies(heracles_data_formats ext_protobuf)
foreach(_protobuf_lib_name ${protobuf_LIB_NAMES})
  target_link_libraries(heracles_data_formats PUBLIC ${_protobuf_lib_name})
endforeach()

install(TARGETS heracles_data_formats
  DESTINATION lib
)

# install and find_package mechanism
set(HERACLES_DATA_FORMATS_TARGET_FILENAME ${PROJECT_BINARY_DIR}/cmake/HERACLES_DATA_FORMATSTargets.cmake)
set(HERACLES_DATA_FORMATS_CONFIG_IN_FILENAME ${HERACLES_DATA_FORMATS_CMAKE_PATH}/HERACLES_DATA_FORMATSConfig.cmake.in)
set(HERACLES_DATA_FORMATS_CONFIG_FILENAME ${PROJECT_BINARY_DIR}/cmake/HERACLES_DATA_FORMATSConfig.cmake)
set(HERACLES_DATA_FORMATS_CONFIG_VERSION_FILENAME ${PROJECT_BINARY_DIR}/cmake/HERACLES_DATA_FORMATSConfigVersion.cmake)
set(HERACLES_DATA_FORMATS_CONFIG_INSTALL_DIR ${CMAKE_INSTALL_LIBDIR}/cmake/HERACLES_DATA_FORMATS-${HERACLES_DATA_FORMATS_VERSION})

install(
  EXPORT HERACLES_DATA_FORMATSTargets
  NAMESPACE HERACLES_DATA_FORMATS::
  DESTINATION ${HERACLES_DATA_FORMATS_CONFIG_INSTALL_DIR}
)

write_basic_package_version_file(
  ${HERACLES_DATA_FORMATS_CONFIG_VERSION_FILENAME}
  VERSION ${HERACLES_DATA_FORMATS_VERSION}
  COMPATIBILITY ExactVersion
)

configure_package_config_file(
  ${HERACLES_DATA_FORMATS_CONFIG_IN_FILENAME} ${HERACLES_DATA_FORMATS_CONFIG_FILENAME}
  INSTALL_DESTINATION ${HERACLES_DATA_FORMATS_CONFIG_INSTALL_DIR}
)

install(
  TARGETS heracles_data_formats
  EXPORT HERACLES_DATA_FORMATSTargets
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin
)

install(
  FILES ${HERACLES_DATA_FORMATS_CONFIG_FILENAME}
        ${HERACLES_DATA_FORMATS_CONFIG_VERSION_FILENAME}
  DESTINATION ${HERACLES_DATA_FORMATS_CONFIG_INSTALL_DIR}
)
# Added to enable non-installation build
export(EXPORT HERACLES_DATA_FORMATSTargets
  NAMESPACE HERACLES_DATA_FORMATS::
  FILE ${HERACLES_DATA_FORMATS_TARGET_FILENAME}
)
