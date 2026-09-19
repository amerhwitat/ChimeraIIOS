@echo off
setlocal
set ROOT=%~dp0..\..
set BUILD=%ROOT%\build\hosted-windows
cmake -S "%ROOT%" -B "%BUILD%" -DCMAKE_BUILD_TYPE=Release -DCHIMERA_EDITION=HOSTED
if errorlevel 1 exit /b %errorlevel%
cmake --build "%BUILD%" --config Release --parallel
if errorlevel 1 exit /b %errorlevel%
ctest --test-dir "%BUILD%" -C Release --output-on-failure
exit /b %errorlevel%
