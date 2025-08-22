add_library(boolexpr STATIC)

add_subdirectory(src)

target_include_directories(boolexpr PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include/boolexpr>
  $<INSTALL_INTERFACE:include>
)

target_compile_features(boolexpr PRIVATE c_std_99)
