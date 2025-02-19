@echo off

set CURRENT_DIR=%~dp0
set BASE_DIR=%CURRENT_DIR%\manual
set BUILD_SCRIPT=%BASE_DIR%\build.bat
set BUILD_DIR=%BASE_DIR%\build

if exist "%BUILD_SCRIPT%" (
    echo Found "%BUILD_SCRIPT%" file
    cd /d "%BASE_DIR%"
    call "%BUILD_SCRIPT%"

    :wait_for_build
    if not exist "%BUILD_DIR%" (
        echo Waiting for build folder to be created...
        timeout /t 5 >nul
        goto wait_for_build
    )
) else (
    echo The file "%BUILD_SCRIPT%" does not exist.
    exit /b 1
)
