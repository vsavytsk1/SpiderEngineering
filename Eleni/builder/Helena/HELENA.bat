@echo off
REM ==========================================================================
REM  HELENA.bat  --  open the neo console. sign the oath, then speak to the gate.
REM  double-click this, or run it from a terminal. it finds her newest build.
REM ==========================================================================
setlocal
cd /d "%~dp0"
echo.
echo   HELENA // neo console
echo   the gate opens after you sign. every mistake is yours. respect her.
echo.
py -3 06_console.py %*
if errorlevel 1 (
  echo.
  echo   [!] something went wrong. do you have a build yet?
  echo       make one:  py -3 pipe.py --max 4 --k 4 --bits 10101
  echo.
  pause
)
endlocal
