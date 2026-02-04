@echo off
echo ============================================
echo 配置 Visual Studio 2022 环境变量
echo ============================================

:: 定义 Visual Studio 2022 安装路径
set "VS_INSTALL_PATH=C:\Program Files\Microsoft Visual Studio\2022\Community"
set "VC_TOOLS_PATH=%VS_INSTALL_PATH%\VC\Tools\MSVC"

:: 查找最新的 MSVC 版本（这里使用找到的最新版本 14.44.35207）
set "MSVC_VERSION=14.44.35207"
set "MSVC_PATH=%VC_TOOLS_PATH%\%MSVC_VERSION%"

:: 检查 MSVC 路径是否存在
if not exist "%MSVC_PATH%\bin\Hostx64\x64" (
    echo 错误：未找到 MSVC 编译器路径：%MSVC_PATH%\bin\Hostx64\x64
    echo 请检查 Visual Studio 2022 是否正确安装
    pause
    exit /b 1
)

echo 找到 MSVC 编译器：%MSVC_VERSION%
echo 路径：%MSVC_PATH%

:: 配置环境变量

:: 1. 编译器路径（x64）
set "PATH=%MSVC_PATH%\bin\Hostx64\x64;%PATH%"

:: 2. 标准库头文件路径
set "INCLUDE=%MSVC_PATH%\include;%INCLUDE%"

:: 3. 库文件路径
set "LIB=%MSVC_PATH%\lib\x64;%LIB%"

:: 4. Windows SDK 路径（Visual Studio 2022 默认包含的 Windows SDK 版本）
:: 查找 Windows SDK 路径（通常在 C:\Program Files (x86)\Windows Kits\10 或 C:\Program Files (x86)\Windows Kits\11）
set "WINDOWS_KITS_PATH=C:\Program Files (x86)\Windows Kits\10"
if not exist "%WINDOWS_KITS_PATH%" (
    set "WINDOWS_KITS_PATH=C:\Program Files (x86)\Windows Kits\11"
)

if exist "%WINDOWS_KITS_PATH%" (
    :: 查找最新的 Windows SDK 版本
    for /f "delims=" %%d in ('dir /b "%WINDOWS_KITS_PATH%\Include"') do (
        set "WINDOWS_SDK_VERSION=%%d"
    )
    
    if defined WINDOWS_SDK_VERSION (
        echo 找到 Windows SDK：%WINDOWS_SDK_VERSION%
        
        :: 添加 Windows SDK 头文件路径
        set "INCLUDE=%WINDOWS_KITS_PATH%\Include\%WINDOWS_SDK_VERSION%\ucrt;%WINDOWS_KITS_PATH%\Include\%WINDOWS_SDK_VERSION%\um;%WINDOWS_KITS_PATH%\Include\%WINDOWS_SDK_VERSION%\shared;%INCLUDE%"
        
        :: 添加 Windows SDK 库文件路径
        set "LIB=%WINDOWS_KITS_PATH%\Lib\%WINDOWS_SDK_VERSION%\um\x64;%WINDOWS_KITS_PATH%\Lib\%WINDOWS_SDK_VERSION%\ucrt\x64;%LIB%"
    )
)

:: 5. .NET Framework 路径（可选）
set "PATH=C:\Windows\Microsoft.NET\Framework64\v4.0.30319;%PATH%"

:: 6. Visual Studio 工具路径
set "PATH=%VS_INSTALL_PATH%\Common7\IDE;%VS_INSTALL_PATH%\Common7\Tools;%PATH%"

echo ============================================
echo 环境变量配置完成！
echo ============================================
echo.
echo 已配置的关键路径：
echo - MSVC 编译器：%MSVC_PATH%\bin\Hostx64\x64
echo - 头文件目录：%MSVC_PATH%\include
echo - 库文件目录：%MSVC_PATH%\lib\x64
if defined WINDOWS_SDK_VERSION (
    echo - Windows SDK：%WINDOWS_SDK_VERSION%
)
echo.
echo 现在可以使用 cl 命令编译 C/C++ 程序了
echo 尝试运行 cl 命令检查：

cl

echo.
echo ============================================