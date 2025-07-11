# Recent release version
set(PROTOBUF_EXT_GIT_TAG v4.23.4)
set(PROTOBUF_EXT_GIT_URL https://github.com/protocolbuffers/protobuf.git)
set(PROTOBUF_EXT_PREFIX ${CMAKE_CURRENT_BINARY_DIR}/ext_protobuf)
set(PROTOBUF_EXT_DESTDIR ${PROTOBUF_EXT_PREFIX}/protobuf_install)

include(ExternalProject)
ExternalProject_Add(
  ext_protobuf
  GIT_REPOSITORY ${PROTOBUF_EXT_GIT_URL}
  GIT_TAG ${PROTOBUF_EXT_GIT_TAG}
  PREFIX ${PROTOBUF_EXT_PREFIX}
  CMAKE_ARGS ${CMAKE_CXX_FLAGS}
             -DCMAKE_INSTALL_PREFIX=${PROTOBUF_EXT_DESTDIR}
             -Dprotobuf_BUILD_EXAMPLES=OFF
             -Dprotobuf_BUILD_TESTS=OFF
             -DABSL_PROPAGATE_CXX_STD=ON
             -DCMAKE_INSTALL_LIBDIR=lib
             -DCMAKE_BUILD_TYPE=Release
             -DCMAKE_INSTALL_RPATH=$ORIGIN
             -Dprotobuf_BUILD_SHARED_LIBS=ON
  UPDATE_COMMAND ""
  INSTALL_COMMAND make install
)


set(protobuf_SOURCE_DIR ${PROTOBUF_EXT_PREFIX}/src/ext_protobuf)
set(protobuf_INCLUDE_DIR ${PROTOBUF_EXT_DESTDIR}/include)
set(protobuf_LIB_DIR ${PROTOBUF_EXT_DESTDIR}/lib)
set(protobuf_BIN_DIR ${PROTOBUF_EXT_DESTDIR}/bin)

# setup protobuf executable
add_executable(protobuf_executable IMPORTED GLOBAL)
add_dependencies(protobuf_executable ext_protobuf)
set_target_properties(protobuf_executable PROPERTIES
  IMPORTED_LOCATION ${protobuf_BIN_DIR}/protoc
)
set(protobuf_PROTOC_EXECUTABLE ${protobuf_BIN_DIR}/protoc)

foreach(_protobuf_lib_name ${protobuf_SHARED_LIB_NAMES})
  set(_protobuf_lib_filename_shared "lib${_protobuf_lib_name}${CMAKE_SHARED_LIBRARY_SUFFIX}")
  add_library(${_protobuf_lib_name} SHARED IMPORTED GLOBAL)
  add_dependencies(${_protobuf_lib_name} ext_protobuf)
  set_target_properties(${_protobuf_lib_name} PROPERTIES
    IMPORTED_LOCATION ${protobuf_LIB_DIR}/${_protobuf_lib_filename_shared}
    INCLUDE_DIRECTORIES ${protobuf_INCLUDE_DIR}
  )
endforeach()

foreach(_protobuf_lib_name ${protobuf_STATIC_LIB_NAMES})
  set(_protobuf_lib_filename_static "lib${_protobuf_lib_name}${CMAKE_STATIC_LIBRARY_SUFFIX}")
  add_library(${_protobuf_lib_name} STATIC IMPORTED GLOBAL)
  add_dependencies(${_protobuf_lib_name} ext_protobuf)
  set_target_properties(${_protobuf_lib_name} PROPERTIES
    IMPORTED_LOCATION ${protobuf_LIB_DIR}/${_protobuf_lib_filename_static}
    INCLUDE_DIRECTORIES ${protobuf_INCLUDE_DIR}
  )
endforeach()

install(DIRECTORY ${protobuf_INCLUDE_DIR}/
  DESTINATION include
)

# copy library and binary files when installing
install(DIRECTORY ${protobuf_LIB_DIR}/
  DESTINATION lib
  USE_SOURCE_PERMISSIONS
)

install(DIRECTORY ${protobuf_BIN_DIR}/
  DESTINATION bin
  USE_SOURCE_PERMISSIONS
)
