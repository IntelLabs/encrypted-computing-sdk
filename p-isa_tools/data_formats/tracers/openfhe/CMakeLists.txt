# Include FetchContent module
include(FetchContent)

# Add OpenFHE via FetchContent
FetchContent_Declare(
    OpenFHE
    GIT_REPOSITORY https://github.com/AlexanderViand/openfhe-development.git
    GIT_TAG 7e2eafc49b6b4c1a0000b1722a8749797ec277d9  # head of `tracing` branch (2025-08-07)
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

# Create executable from tracing_example.cpp
add_executable(tracing_example tracing_example.cpp tracer.h)
# Set C++ standard
target_compile_features(tracing_example PRIVATE cxx_std_17)
# Link with OpenFHE libraries
target_link_libraries(tracing_example PRIVATE HERACLES_DATA_FORMATS::heracles_data_formats OPENFHEcore OPENFHEpke OPENFHEbinfhe)

target_include_directories(tracing_example PRIVATE
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
target_compile_options(tracing_example PRIVATE
    $<$<CONFIG:Release>:-O3>
    $<$<CONFIG:Debug>:-g -O0>
)


# define a custom target that runs tracing, then submits the trace to the program mapper, finally sending the pisa and mem file to the functional modeler
add_custom_target(
  run_tracing_example
  # Run the actual example, which will generate the traces as end-to-end-test/tracing_example.bin and end-to-end-test/tracing_example_data.bin
  COMMAND ${CMAKE_COMMAND} -E echo "[INFO] Running tracing_example:" $<TARGET_FILE:tracing_example>
  COMMAND ${CMAKE_COMMAND} -E echo "[INFO] Traces can be found in: ${CMAKE_BINARY_DIR}/end-to-end-test/"
  COMMAND tracing_example
  # Run the program mapper on the instruction trace, generating end-to-end-test/tracing_example.bin.csv
  COMMAND ${CMAKE_COMMAND} -E echo "[INFO] Running program_mapper."
  COMMAND env VIRTUAL_ENV=${VENV_PATH} PATH=${VENV_PATH}/bin:$ENV{PATH} PYTHONPATH=${VENV_SITE_PACKAGES}:$ENV{PYTHONPATH} $<TARGET_FILE:program_mapper> ${CMAKE_BINARY_DIR}/end-to-end-test/tracing_example.bin ${CMAKE_SOURCE_DIR}/kerngen/kerngen.py
  COMMAND ${CMAKE_COMMAND} -E echo "[INFO] Running functional_modeler:"
  COMMAND $<TARGET_FILE:functional_modeler> ${CMAKE_BINARY_DIR}/end-to-end-test/tracing_example_pisa.csv --verbose --hec_dataformats_mode --hec_dataformats_poly_program_location ${CMAKE_BINARY_DIR}/end-to-end-test/tracing_example.bin --hec_dataformats_data ${CMAKE_BINARY_DIR}/end-to-end-test/tracing_example_data.bin
  # TODO: Next step: assemble the *.pisa.csv and the *tw.mem using the assembler from https://github.com/IntelLabs/HERACLES-HGCF
  # TODO: Then it's a dead end :( as we don't have any tooling that can support non-toy sized workloads
  DEPENDS tracing_example program_mapper functional_modeler create-end-to-end-test-dir
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/end-to-end-test
)

add_custom_target(create-end-to-end-test-dir
  COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/end-to-end-test
  COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/end-to-end-test
)
