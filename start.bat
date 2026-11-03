@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 (
    echo Could not open the project folder.
    exit /b 1
)

set "INSTALL_DEPS=1"
set "UPGRADE_PIP=1"

:parse_args
if "%~1"=="" goto args_done
if /i "%~1"=="--install" (
    set "INSTALL_DEPS=1"
    shift
    goto parse_args
)
if /i "%~1"=="--no-install" (
    set "INSTALL_DEPS=0"
    shift
    goto parse_args
)
if /i "%~1"=="--upgrade" (
    set "UPGRADE_PIP=1"
    shift
    goto parse_args
)
if /i "%~1"=="--no-upgrade" (
    set "UPGRADE_PIP=0"
    shift
    goto parse_args
)
if /i "%~1"=="--help" goto help
if /i "%~1"=="-h" goto help
echo Unknown option: %~1
echo Use start.bat --help for available options.
exit /b 2

:args_done
set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=python"
)
if not defined PYTHON_CMD goto python_missing

echo.
echo ========================================
echo Lupin launcher
echo Python: %PYTHON_CMD%
echo Dependencies are installed for the current user.
echo No virtual environment is created or used.
echo ========================================

if "%INSTALL_DEPS%"=="0" goto launch
if not exist "requirements.txt" goto requirements_missing

%PYTHON_CMD% -m pip --version >nul 2>nul
if not errorlevel 1 goto pip_ready

echo pip is missing. Trying to enable it with ensurepip...
%PYTHON_CMD% -m ensurepip --upgrade
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto pip_missing

:pip_ready
if "%UPGRADE_PIP%"=="0" goto install_dependencies
echo.
echo Updating pip...
%PYTHON_CMD% -m pip install --user --upgrade pip
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto install_failed

:install_dependencies
echo.
echo Installing dependencies from requirements.txt...
%PYTHON_CMD% -m pip install --user -r "requirements.txt"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto install_failed

:launch
if not exist "start.py" goto app_missing
echo.
echo Starting Lupin...
%PYTHON_CMD% "start.py"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" goto app_failed
exit /b 0

:help
echo Lupin launcher options:
echo   --install      Install requirements before launching (default)
echo   --no-install   Skip dependency installation
echo   --upgrade      Upgrade pip before installing (default)
echo   --no-upgrade   Skip pip upgrade
echo   --help, -h     Show this help
echo.
echo Examples:
echo   start.bat
echo   start.bat --no-upgrade
echo   start.bat --no-install
exit /b 0

:python_missing
echo Python 3 was not found. Install Python and add it to PATH.
pause
exit /b 1

:requirements_missing
echo requirements.txt was not found in the project folder.
pause
exit /b 1

:pip_missing
echo pip could not be enabled. Repair or reinstall Python with pip included.
pause
exit /b 1

:install_failed
echo Dependency installation failed with exit code %RESULT%.
echo Check your internet connection and Python installation.
pause
exit /b %RESULT%

:app_missing
echo start.py was not found in the project folder.
pause
exit /b 1

:app_failed
echo The application exited with error code %RESULT%.
pause
exit /b %RESULT%
