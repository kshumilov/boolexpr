python_add_library(
  core MODULE
  ${CMAKE_CURRENT_SOURCE_DIR}/main.c
  WITH_SOABI
)

add_subdirectory(core)

target_link_libraries(core PRIVATE boolexpr)

install(TARGETS core DESTINATION ${SKBUILD_PROJECT_NAME})
