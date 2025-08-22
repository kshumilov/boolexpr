python_add_library(
  exprnode MODULE
  ${CMAKE_CURRENT_SOURCE_DIR}/exprnodemodule.c
  WITH_SOABI
)

add_subdirectory(exprnode)

target_link_libraries(exprnode PRIVATE boolexpr)

install(TARGETS exprnode DESTINATION ${SKBUILD_PROJECT_NAME})
