@echo off
setlocal EnableExtensions
title EEG Paradox EDF Tool

REM Monorepo: .../<repo>/EEG_EDF_Standalone_Tool/Run_EDF_Studio.bat
REM Flat GH repo: Run_EDF_Studio.bat next to main.py

pushd "%~dp0" || (
  echo Could not open script folder.
  pause
  exit /b 1
)
set "TOOL_DIR=%CD%"
for %%I in ("%CD%") do set "TOOL_LEAF=%%~nxI"
if /I "%TOOL_LEAF%"=="EEG_EDF_Standalone_Tool" (
  pushd ".." || (
    echo Could not open parent repository folder.
    pause
    exit /b 1
  )
  set "ROOT=%CD%"
  popd
  set "MAIN_PY=%TOOL_DIR%\main.py"
) else (
  set "ROOT=%TOOL_DIR%"
  set "MAIN_PY=%TOOL_DIR%\main.py"
)
popd

set "VENV_PY=%ROOT%\.venv_edf_app\Scripts\python.exe"

if not exist "%VENV_PY%" (
  echo Virtual environment not found.
  echo Double-click One_Click_Setup.bat first to install Python dependencies.
  echo.
  pause
  exit /b 1
)

if not exist "%MAIN_PY%" (
  echo Missing main script:
  echo   %MAIN_PY%
  pause
  exit /b 1
)

"%VENV_PY%" "%MAIN_PY%"
if errorlevel 1 (
  echo.
  echo The application exited with an error code.
  pause
)
exit /b 0
