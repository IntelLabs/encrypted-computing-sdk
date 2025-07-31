target_sources(heracles_data_formats
  PRIVATE
  ${CMAKE_CURRENT_LIST_DIR}/heracles/data/io.cpp
  ${CMAKE_CURRENT_LIST_DIR}/heracles/data/transform.cpp
  ${CMAKE_CURRENT_LIST_DIR}/heracles/data/math.cpp
  ${CMAKE_CURRENT_LIST_DIR}/heracles/util/util.cpp
  ${CMAKE_CURRENT_LIST_DIR}/heracles/fhe_trace/io.cpp
)

target_include_directories(heracles_data_formats
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/>
  PUBLIC $<INSTALL_INTERFACE:include>
)
target_link_libraries(heracles_data_formats
    PRIVATE OpenMP::OpenMP_CXX
)
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/include/
  DESTINATION include
  FILES_MATCHING
  PATTERN "*.h"
)
