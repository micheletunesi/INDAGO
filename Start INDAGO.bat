@echo off
setlocal
title INDAGO
cd /d "%~dp0"

where python >nul 2>nul
if not errorlevel 1 (
    python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "INDAGO_PYTHON=python"
        goto check_dependencies
    )
)

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "INDAGO_PYTHON=py -3"
        goto check_dependencies
    )
)

echo Python 3.10 or newer was not found.
echo Install Python with Tkinter and enable "Add python.exe to PATH".
echo Then double-click this launcher again.
goto failed

:check_dependencies
%INDAGO_PYTHON% -c "import tkinter, matplotlib" >nul 2>nul
if errorlevel 1 (
    echo A required component is missing. Run these commands in this folder:
    echo.
    echo     %INDAGO_PYTHON% -m pip install -r requirements.txt
    echo.
    echo If Tkinter is missing, modify your Python installation to include Tcl/Tk.
    goto failed
)

%INDAGO_PYTHON% indago_app.py
if errorlevel 1 goto failed
exit /b 0

:failed
echo.
echo The application could not start. Review the message above.
pause
exit /b 1
