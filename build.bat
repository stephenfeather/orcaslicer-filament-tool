@echo off
REM Build standalone executable with Nuitka

echo Building OrcaSlicer Filament Tool standalone executable...

REM Check if Nuitka is installed
python -c "import nuitka" 2>nul
if errorlevel 1 (
    echo Installing Nuitka...
    pip install nuitka
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist orcaslicer-export.build rmdir /s /q orcaslicer-export.build
if exist orcaslicer-export.dist rmdir /s /q orcaslicer-export.dist

REM Build with Nuitka
echo Compiling with Nuitka...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --output-filename=orcaslicer-export.exe ^
    --output-dir=dist ^
    --include-package=src ^
    --assume-yes-for-downloads ^
    --remove-output ^
    src/cli.py

echo.
echo Build complete!
echo   Executable: dist\orcaslicer-export.exe
echo.
echo Test the executable:
echo   dist\orcaslicer-export.exe --help
