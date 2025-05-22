################################
# P-ISA Tools Main Entrypoint
################################

cmake_minimum_required(VERSION 3.22)

# General Setup
if(CMAKE_BUILD_TYPE)
  set(RELEASE_TYPES
      Debug
      Release
      RelWithDebInfo
      MinSizeRel)
  list(FIND RELEASE_TYPES ${CMAKE_BUILD_TYPE} INDEX_FOUND)
  if(${INDEX_FOUND} EQUAL -1)
    message(
      FATAL_ERROR
        "CMAKE_BUILD_TYPE must be one of Debug, Release, RelWithDebInfo, or MinSizeRel"
      )
  endif()
else()
  set(CMAKE_BUILD_TYPE "Debug" CACHE STRING "Choose the type of Build" FORCE)
endif()

option(ENABLE_DATA_FORMATS "Enable support for the data formats library" OFF)
message(ENABLE_DATA_FORMATS="${ENABLE_DATA_FORMATS}")

option(ENABLE_FUNCTIONAL_MODELER "Enable building of functional modeler" ON)
message(ENABLE_FUNCTIONAL_MODELER="${ENABLE_FUNCTIONAL_MODELER}")

option(ENABLE_PROGRAM_MAPPER "Enable building of program mapper" OFF)
message(ENABLE_PROGRAM_MAPPER="${ENABLE_PROGRAM_MAPPER}")

option(ENABLE_P_ISA_UTILITIES "Enable building of p-isa utilities" OFF)
message(ENABLE_P_ISA_UTILITIES="${ENABLE_P_ISA_UTILITIES}")

configure_file(common/config.h.in "${CMAKE_BINARY_DIR}/p_isa_tools_config/config.h")

project(p_isa_tools LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Define standard installation directories (GNU)
include(GNUInstallDirs)

# Set default output directories
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_LIBDIR}")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/${CMAKE_INSTALL_BINDIR}")

# Find OpenMP on system
find_package(OpenMP REQUIRED)

# External fetch and build dependencies
include(cmake/dependencies.cmake)

# Policy is explicit header locations
set(INCLUDE_DIRS ${PROJECT_SOURCE_DIR} ${CMAKE_BINARY_DIR}/p_isa_tools_config/)

# Include *.h files in sources so they appear in IDEs
file(GLOB_RECURSE IDE_HEADERS program_mapper/*.h functional_modeler/*.h dependencies/*.h common/*.h)

# Build sub-directories
add_subdirectory(common)
if(ENABLE_FUNCTIONAL_MODELER)
add_subdirectory(functional_modeler)
endif()
if(ENABLE_PROGRAM_MAPPER)
add_subdirectory(program_mapper)
endif()
if(ENABLE_P_ISA_UTILITIES)
add_subdirectory(p_isa_utilities)
endif()
