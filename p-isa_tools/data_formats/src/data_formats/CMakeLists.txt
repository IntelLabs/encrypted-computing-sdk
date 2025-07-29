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
