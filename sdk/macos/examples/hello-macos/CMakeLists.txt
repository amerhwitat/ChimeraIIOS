cmake_minimum_required(VERSION 3.20)
project(HelloMacOS LANGUAGES C OBJC)
add_executable(HelloMacOS main.m)
set_target_properties(HelloMacOS PROPERTIES MACOSX_BUNDLE TRUE)
