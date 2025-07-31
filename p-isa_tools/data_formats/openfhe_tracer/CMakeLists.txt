# Include FetchContent module
include(FetchContent)

# Add OpenFHE via FetchContent
FetchContent_Declare(
    OpenFHE
    GIT_REPOSITORY https://github.com/AlexanderViand/openfhe-development.git
    GIT_TAG 274e470b99495d571a1f6008578601b99e569d84  # head of `tracing` branch (2025-07-28)
)

# Set OpenFHE build options before making it available
set(BUILD_UNITTESTS OFF CACHE BOOL "" FORCE)
set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_BENCHMARKS OFF CACHE BOOL "" FORCE)
set(ENABLE_TRACER ON CACHE BOOL "" FORCE)

message(STATUS "Fetching OpenFHE, this may take a while...")
FetchContent_MakeAvailable(OpenFHE)
message(STATUS "Finished configuring OpenFHE")

FetchContent_GetProperties(openfhe)

# Create executable from simple_tracing.cpp
add_executable(simple_tracing simple_tracing.cpp heraclestracer.h)
# Set C++ standard
target_compile_features(simple_tracing PRIVATE cxx_std_17)
# Link with OpenFHE libraries
target_link_libraries(simple_tracing PRIVATE HERACLES_DATA_FORMATS::heracles_data_formats OPENFHEcore OPENFHEpke OPENFHEbinfhe)

target_include_directories(simple_tracing PRIVATE
    # Third Party Includes
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/third-party/include>
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/third-party/cereal/include>
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/third-party/google-test/googletest>
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/third-party/google-test/googletest/include>
    # public headers that sit in the repo
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/src/core/include>
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/src/pke/include>
    $<BUILD_INTERFACE:${openfhe_SOURCE_DIR}/src/binfhe/include>
    # generated header  (configure_file → config_core.h)
    $<BUILD_INTERFACE:${openfhe_BINARY_DIR}/src/core>)


# Set compiler flags for optimization and debug info
target_compile_options(simple_tracing PRIVATE
    $<$<CONFIG:Release>:-O3>
    $<$<CONFIG:Debug>:-g -O0>
)


# define a custom target that runs tracing, then submits the trace to the program mapper, finally sending the pisa and mem file to the functional modeler
add_custom_target(
  run_simple_tracing
  # Run the actual example, which will generate the traces as end-to-end-test/simple_tracing.bin and end-to-end-test/simple_tracing_data.bin
  COMMAND simple_tracing
  # Run the program mapper on the instruction trace, generating end-to-end-test/simple_tracing.bin.csv
  COMMAND env VIRTUAL_ENV=${VENV_PATH} PATH=${VENV_PATH}/bin:$ENV{PATH} PYTHONPATH=${VENV_SITE_PACKAGES}:$ENV{PYTHONPATH} $<TARGET_FILE:program_mapper> ${CMAKE_BINARY_DIR}/end-to-end-test/simple_tracing.bin ${CMAKE_SOURCE_DIR}/kerngen/kerngen.py
  COMMAND $<TARGET_FILE:functional_modeler> ${CMAKE_BINARY_DIR}/end-to-end-test/simple_tracing_pisa.csv --verbose --hec_dataformats_mode --hec_dataformats_poly_program_location ${CMAKE_BINARY_DIR}/end-to-end-test/simple_tracing.bin --hec_dataformats_data ${CMAKE_BINARY_DIR}/end-to-end-test/simple_tracing_data.bin
  # TODO: Next step: assemble the *.pisa.csv and the *tw.mem using the assembler from https://github.com/IntelLabs/HERACLES-HGCF
  # TODO: Then it's a dead end :( as we don't have any tooling that can support non-toy sized workloads
  DEPENDS simple_tracing program_mapper functional_modeler create-end-to-end-test-dir
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/end-to-end-test
)

add_custom_target(create-end-to-end-test-dir
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/end-to-end-test
  COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/end-to-end-test
)
