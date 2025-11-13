@echo off
cls

set INPUT_UI_FILE=ui\main.ui
set OUTPUT_PY_FILE=scripts\ui\mainUI.py

echo Activating Python Virtual Environment...
:: ----------------------------------------------------------------------
:: FIX 1: Use the BATCH activation script (e.g., 'activate.bat' or 'activate.cmd')
:: and use 'call' to run it within the current cmd.exe session.
:: ----------------------------------------------------------------------
call ..\Scripts\activate.bat

echo.
echo Converting %INPUT_UI_FILE% to %OUTPUT_PY_FILE%

:: Ensure pyuic5 is available in the virtual environment's PATH
pyside6-uic "%INPUT_UI_FILE%" -o "%OUTPUT_PY_FILE%"
pyside6-rcc scripts\ui\icons_resource.qrc -o scripts\ui\icons_resource_rc.py
echo.
echo Deactivating Virtual Environment...
:: Deactivate the environment after the conversion is done
deactivate

echo.
echo Conversion process finished.
pause

@REM @echo off
@REM cls

@REM set INPUT_UI_FILE=code\ui\main.ui
@REM set OUTPUT_PY_FILE=code\scripts\ui\mainUI.py
@REM set INPUT_QRC_FILE=code\ui\resources.qrc
@REM set OUTPUT_RC_FILE=code\scripts\ui\main_rc.py

@REM echo Activating Python Virtual Environment...
@REM :: ----------------------------------------------------------------------
@REM :: Use the BATCH activation script (e.g., 'activate.bat' or 'activate.cmd')
@REM :: and use 'call' to run it within the current cmd.exe session.
@REM :: ----------------------------------------------------------------------
@REM call ..\Scripts\activate.bat

@REM echo.
@REM echo Converting %INPUT_UI_FILE% to %OUTPUT_PY_FILE%

@REM :: Ensure pyuic5 is available in the virtual environment's PATH
@REM pyuic5 -x "%INPUT_UI_FILE%" -o "%OUTPUT_PY_FILE%"

@REM echo.
@REM echo Compiling Icons/Resources from %INPUT_QRC_FILE% to %OUTPUT_RC_FILE%

@REM :: ----------------------------------------------------------------------
@REM :: NEW STEP: Run pyrcc5 to compile the Qt Resource file (.qrc)
@REM :: ----------------------------------------------------------------------
@REM pyrcc5 "%INPUT_QRC_FILE%" -o "%OUTPUT_RC_FILE%"

@REM echo.
@REM echo Deactivating Virtual Environment...
@REM deactivate

@REM echo.
@REM echo Conversion and Compilation finished.
@REM pause
