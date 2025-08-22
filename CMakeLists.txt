cmake_minimum_required(VERSION 3.15...3.31)
project(${SKBUILD_PROJECT_NAME} LANGUAGES C)

find_package(
  Python
  COMPONENTS Development.Module
  REQUIRED
)

python_add_library(core MODULE src/main.c WITH_SOABI)

install(TARGETS core DESTINATION ${SKBUILD_PROJECT_NAME})
