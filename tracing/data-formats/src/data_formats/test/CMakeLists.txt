# HERACLES_data_proto test
add_executable(heracles_test
  heracles_test.cpp
)
target_link_libraries(heracles_test PRIVATE heracles_data_formats)
add_test(
  NAME heracles_proto_c++
  COMMAND ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/heracles_test
  WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
)
set(Python3_FIND_VIRTUALENV FIRST)
find_package(Python3 REQUIRED COMPONENTS Interpreter)
add_test(
  NAME heracles_test_python
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/heracles_test.py
  WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
)

set_tests_properties(heracles_test_python PROPERTIES
  ENVIRONMENT "PYTHONPATH=${PROJECT_BINARY_DIR}/python:$ENV{PYTHONPATH}"
)

add_executable(heracles_math_test
  heracles_math_test.cpp
  math_unittest/unittest.cpp
)

target_link_libraries(heracles_math_test PRIVATE heracles_data_formats)
add_test(
  NAME heracles_math_UNITTEST
  COMMAND ${CMAKE_RUNTIME_OUTPUT_DIRECTORY}/heracles_math_test
  WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
)
