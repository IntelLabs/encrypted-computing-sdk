
include(FetchContent)
FetchContent_Declare(
   json_for_modern_cpp
   # v3.11.2 released Aug 2023
   URL https://github.com/nlohmann/json/releases/download/v3.11.2/json.tar.xz
   URL_HASH SHA256=8c4b26bf4b422252e13f332bc5e388ec0ab5c3443d24399acb675e68278d341f
)

FetchContent_MakeAvailable(json_for_modern_cpp)

FetchContent_Declare(
    argmap
    # TODO at the mo, grabs the latest this should change once versioned
    URL https://raw.githubusercontent.com/helibproject/argmap/main/argmap.h
    DOWNLOAD_NO_EXTRACT TRUE
)

FetchContent_GetProperties(argmap)
if (NOT argmap_POPULATED)
    FetchContent_Populate(argmap)
    include_directories(${argmap_SOURCE_DIR})
endif()

FetchContent_Declare(
    snap
    # commit from Feb 2023
    GIT_REPOSITORY https://github.com/snap-stanford/snap.git
    GIT_TAG 6924a035aabd1ce0a547b94e995e142f29eb5040
)

FetchContent_GetProperties(snap)
if (NOT snap_POPULATED)
    FetchContent_Populate(snap)
    message(STATUS "Building SNAP, this may take a while ...")
    execute_process(COMMAND make -j
                    WORKING_DIRECTORY ${snap_SOURCE_DIR}
                    OUTPUT_QUIET
                    ERROR_QUIET
                    OUTPUT_FILE ${FETCHCONTENT_BASE_DIR}/snap.stdout
                    ERROR_FILE ${FETCHCONTENT_BASE_DIR}/snap.stderr
    )
    add_library(snap OBJECT IMPORTED GLOBAL)
    set_target_properties(snap PROPERTIES IMPORTED_OBJECTS ${snap_SOURCE_DIR}/snap-core/Snap.o)
    include_directories(${snap_SOURCE_DIR}/snap-core ${snap_SOURCE_DIR}/glib-core)
    message(STATUS "Finished building SNAP")
endif()

if(ENABLE_DATA_FORMATS)
    find_package(HERACLES_DATA_FORMATS CONFIG)
    if(NOT HERACLES_DATA_FORMATS_FOUND)
        FetchContent_Declare(
            heracles_data_formats
            GIT_REPOSITORY git@github.com:IntelLabs/HERACLES-data-formats.git
            GIT_TAG main
        )
        FetchContent_MakeAvailable(heracles_data_formats)
    endif()
endif()
