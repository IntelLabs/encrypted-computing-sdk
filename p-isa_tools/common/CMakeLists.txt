##################
# HERACLES Utils
##################

project(common)

set(SRCS
  p_isa/p_isa_instruction.cpp
  p_isa/parser/p_isa_parser.cpp
  p_isa/p_isa_performance_modeler.h
  p_isa/p_isa_performance_modeler.cpp
)

add_library(common OBJECT ${SRCS})
target_include_directories(common PRIVATE ${INCLUDE_DIRS})
