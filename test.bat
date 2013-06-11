@echo off
IF NOT EXIST C:\Python27\python.exe (IF "%2"=="" (goto getinterp) ELSE (set INTERP=%2)) ELSE (set INTERP=C:\Python27\python.exe)
goto run
:getinterp
echo No Python interpreter found at the default location. Check to ensure that a 32-bit Python2.7 is installed.
echo If you don't have one, press enter to cancel. Otherwise, specify the full path; on the command line, you can also use the second argument for scripting purposes on your local machine.
set /p INTERP="Enter full path to interpreter, or blank to cancel: "
if "%INTERP%"=="" goto eof
:run
if "%1"=="" (set /p FILE="Enter the .py file to run: ") else (set FILE=%1)
%INTERP% %FILE%
:eof
echo on