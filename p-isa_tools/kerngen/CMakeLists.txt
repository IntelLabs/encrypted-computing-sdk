message( STATUS "Installing kerngen Python requirements")
# First, ensure that we have python3:
find_package (Python3 COMPONENTS Interpreter)

# Now create a venv
set(VENV_PATH "${CMAKE_BINARY_DIR}/venv")
if (NOT EXISTS "${VENV_PATH}/bin/python")
    execute_process(COMMAND "${Python3_EXECUTABLE}" -m venv "${VENV_PATH}"
    RESULT_VARIABLE VENV_CREATION_FAILED)
    if (VENV_CREATION_FAILED)
        message(FATAL_ERROR "Failed to create virtual environment at ${VENV_PATH}")
    endif()
endif()

# Now find python again, but from the venv. This requires (re)setting a few things:
set(Python3_FIND_VIRTUALENV FIRST)
set(Python3_EXECUTABLE "${VENV_PATH}/bin/python")
unset(Python3_VERSION)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

# Make sure we have pip/setup tools
execute_process(COMMAND "${Python3_EXECUTABLE}" -m ensurepip)
execute_process(COMMAND "${Python3_EXECUTABLE}" -m pip install --upgrade pip setuptools)

# Install the requirements
execute_process(COMMAND "${Python3_EXECUTABLE}" -m pip install -r "${CMAKE_CURRENT_LIST_DIR}/requirements.txt")

# Get the site-packages directory for PYTHONPATH
execute_process(
    COMMAND "${Python3_EXECUTABLE}" -c "import site; print(site.getsitepackages()[0])"
    OUTPUT_VARIABLE VENV_SITE_PACKAGES
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

# Make the variables available to parent scope
set(VENV_PATH "${VENV_PATH}" PARENT_SCOPE)
set(VENV_SITE_PACKAGES "${VENV_SITE_PACKAGES}" PARENT_SCOPE)
