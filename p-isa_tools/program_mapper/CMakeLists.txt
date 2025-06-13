##############################
# HERACLES Program Mapper
##############################

project(program_mapper LANGUAGES CXX)

set(HERACLES_PGM_SOURCES
    "p_isa/pisakernel.cpp"
    "p_isa/pisa_graph_optimizer.cpp"
    "poly_program/polyprogram.cpp"
    "trace_parser/program_trace_helper.cpp"
    "p_isa/pisa_test_generator.cpp"
    "utility_functions.h"
    "main.cpp"
)

add_executable(program_mapper ${HERACLES_PGM_SOURCES} ${IDE_HEADERS})
if(ENABLE_DATA_FORMATS)
    target_link_libraries(program_mapper PUBLIC HERACLES_DATA_FORMATS::heracles_data_formats)
    target_compile_definitions(program_mapper PRIVATE ENABLE_DATA_FORMATS)
endif()
target_link_libraries(program_mapper PUBLIC nlohmann_json::nlohmann_json snap OpenMP::OpenMP_CXX common)
target_include_directories(program_mapper PRIVATE ${INCLUDE_DIRS})
