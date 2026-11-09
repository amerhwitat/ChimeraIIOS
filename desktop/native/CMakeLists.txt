# Optional native graphics and vision utilities.
# The base OS remains buildable without these host development packages; when
# OpenGL/GLFW or OpenCV are present, the corresponding tools become installable.
find_package(OpenGL QUIET)
find_package(glfw3 QUIET)
find_package(OpenCV QUIET COMPONENTS core imgcodecs imgproc)

if(OpenGL_FOUND AND (TARGET glfw OR TARGET glfw3::glfw))
  add_executable(chm-opengl-smoke chm-opengl-smoke.cpp)
  target_compile_features(chm-opengl-smoke PRIVATE cxx_std_17)
  if(TARGET glfw)
    target_link_libraries(chm-opengl-smoke PRIVATE glfw OpenGL::GL)
  else()
    target_link_libraries(chm-opengl-smoke PRIVATE glfw3::glfw OpenGL::GL)
  endif()
  install(TARGETS chm-opengl-smoke RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
else()
  message(STATUS "OpenGL smoke utility skipped: OpenGL and GLFW development packages are optional")
endif()

if(OpenCV_FOUND)
  add_executable(chm-image-inspect chm-image-inspect.cpp)
  target_compile_features(chm-image-inspect PRIVATE cxx_std_17)
  target_include_directories(chm-image-inspect PRIVATE ${OpenCV_INCLUDE_DIRS})
  target_link_libraries(chm-image-inspect PRIVATE ${OpenCV_LIBS})
  install(TARGETS chm-image-inspect RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
else()
  message(STATUS "OpenCV image inspector skipped: OpenCV development package is optional")
endif()

install(FILES
  ${CMAKE_CURRENT_SOURCE_DIR}/../../man/chm-opengl-smoke.1
  ${CMAKE_CURRENT_SOURCE_DIR}/../../man/chm-image-inspect.1
  ${CMAKE_CURRENT_SOURCE_DIR}/../../man/chm-ide.1
  ${CMAKE_CURRENT_SOURCE_DIR}/../../man/chm-run-binary.1
  ${CMAKE_CURRENT_SOURCE_DIR}/../../man/chm-toolchains.1
  DESTINATION ${CMAKE_INSTALL_MANDIR}/man1
)
