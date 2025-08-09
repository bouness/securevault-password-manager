@echo off
REM Build script for SecureVault on Windows

REM Clean previous builds
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul
rmdir /s /q installer_output 2>nul

REM Install application dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 exit /b %errorlevel%

REM Install build tool (Nuitka)
pip install nuitka
if %errorlevel% neq 0 exit /b %errorlevel%


REM Build with Nuitka
python -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-qt-plugins=sensible,iconengines,imageformats,platforms,styles,tls,qml ^
    --include-data-dir=src/assets=assets ^
    --include-data-file=version.py=version.py ^
    --include-data-file=LICENSE=LICENSE ^
    --include-data-file=README.md=README.md ^
    --windows-icon-from-ico=src/assets/icon.ico ^
    --output-dir=dist ^
    src/main.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo Nuitka build complete!

REM Call Inno Setup to create the installer
echo Building installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" main.iss
if %errorlevel% neq 0 exit /b %errorlevel%

echo Installer created successfully!

REM Create portable ZIP
echo Creating portable ZIP...
if not exist "dist\main.dist\" (
    echo Error: main.dist directory not found!
    exit /b 1
)
powershell -Command "Compress-Archive -Path 'dist\main.dist\*' -DestinationPath 'dist\SecureVault-Windows-Portable.zip' -Force"
if %errorlevel% neq 0 exit /b %errorlevel%

echo Build completed successfully!