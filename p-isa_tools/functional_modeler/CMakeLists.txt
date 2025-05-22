##############################
# HERACLES Functional Modeler
##############################

project(functional_modeler LANGUAGES CXX)

set(${PROJECT_NAME}_SOURCES
    "main.cpp"
)

add_executable(functional_modeler ${${PROJECT_NAME}_SOURCES} ${IDE_HEADERS})
target_include_directories(functional_modeler PRIVATE ${INCLUDE_DIRS})
target_link_libraries(functional_modeler PUBLIC nlohmann_json::nlohmann_json snap OpenMP::OpenMP_CXX common)
if(ENABLE_DATA_FORMATS)
    target_link_libraries(functional_modeler PUBLIC HERACLES_DATA_FORMATS::heracles_data_formats)
endif()
