# OpenCV C++ 安装指南

## Windows 平台安装

### 方法一：使用预编译库（推荐）

#### 1. 下载 OpenCV

1. 访问 [OpenCV 官方下载页面](https://opencv.org/releases/)
2. 下载最新版本的 Windows 预编译库
3. 解压到 `C:\opencv` 目录

#### 2. 配置环境变量

```batch
# 设置 OpenCV 根目录
setx OPENCV_DIR "C:\opencv\build"

# 添加到系统 PATH
setx PATH "%PATH%;C:\opencv\build\x64\vc15\bin"
```

#### 3. 验证安装

```batch
# 检查环境变量
echo %OPENCV_DIR%

# 测试 DLL 文件
dir %OPENCV_DIR%\x64\vc15\bin\*.dll
```

### 方法二：使用 vcpkg

```batch
# 安装 vcpkg（如果未安装）
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg
.\bootstrap-vcpkg.bat

# 安装 OpenCV
.\vcpkg install opencv4

# 集成到 Visual Studio
.\vcpkg integrate install
```

### 方法三：从源码编译

#### 1. 安装依赖

```batch
# 安装 CMake
# 下载地址：https://cmake.org/download/

# 安装 Visual Studio 2019 或更新版本
```

#### 2. 编译 OpenCV

```batch
# 下载源码
git clone https://github.com/opencv/opencv.git
git clone https://github.com/opencv/opencv_contrib.git

# 创建构建目录
cd opencv
mkdir build
cd build

# 配置 CMake
cmake -D CMAKE_BUILD_TYPE=Release ^
      -D CMAKE_INSTALL_PREFIX=C:\opencv ^
      -D OPENCV_EXTRA_MODULES_PATH=..\..\opencv_contrib\modules ^
      -D BUILD_EXAMPLES=ON ^
      -D BUILD_DOCS=ON ^
      -D BUILD_TESTS=ON ^
      ..

# 编译
cmake --build . --config Release --target install
```

## Linux 平台安装

### Ubuntu/Debian

#### 方法一：使用包管理器

```bash
# 更新包管理器
sudo apt update

# 安装 OpenCV
sudo apt install libopencv-dev python3-opencv

# 验证安装
pkg-config --modversion opencv4
```

#### 方法二：使用 pip

```bash
# 安装 Python 版本
pip3 install opencv-python opencv-contrib-python

# 验证安装
python3 -c "import cv2; print(cv2.__version__)"
```

#### 方法三：从源码编译

```bash
# 安装依赖
sudo apt install build-essential cmake pkg-config
sudo apt install libjpeg-dev libtiff5-dev libpng-dev
sudo apt install libavcodec-dev libavformat-dev libswscale-dev
sudo apt install libgtk2.0-dev libgtk-3-dev
sudo apt install libcanberra-gtk-module libcanberra-gtk3-module
sudo apt install python3-dev python3-numpy

# 下载源码
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.x.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.x.zip

# 解压
unzip opencv.zip
unzip opencv_contrib.zip

# 编译
cd opencv-4.x
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=/usr/local \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-4.x/modules \
      -D BUILD_EXAMPLES=ON ..
make -j4
sudo make install
```

### CentOS/RHEL

```bash
# 安装 EPEL 仓库
sudo yum install epel-release
sudo yum update

# 安装依赖
sudo yum install gcc gcc-c++ cmake3
sudo yum install gtk2-devel libpng-devel jasper-devel openexr-devel
sudo yum install libwebp-devel libjpeg-turbo-devel libtiff-devel
sudo yum install tbb-devel eigen3-devel

# 编译安装（类似 Ubuntu 步骤）
```

## macOS 平台安装

### 方法一：使用 Homebrew

```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 OpenCV
brew install opencv

# 验证安装
pkg-config --modversion opencv4
```

### 方法二：使用 MacPorts

```bash
# 安装 MacPorts（如果未安装）
# 下载地址：https://www.macports.org/install.php

# 安装 OpenCV
sudo port install opencv4

# 验证安装
pkg-config --modversion opencv4
```

### 方法三：从源码编译

```bash
# 安装依赖
brew install cmake pkg-config
brew install jpeg tiff libpng
brew install eigen tbb

# 下载源码并编译（类似 Linux 步骤）
```

## 验证安装

### C++ 测试程序

创建测试文件 `test_opencv.cpp`：

```cpp
#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    std::cout << "OpenCV 版本: " << CV_VERSION << std::endl;
    
    // 创建一个简单的图像
    cv::Mat image = cv::Mat::zeros(100, 100, CV_8UC3);
    cv::circle(image, cv::Point(50, 50), 30, cv::Scalar(255, 0, 0), -1);
    
    // 保存图像
    cv::imwrite("test_output.png", image);
    
    std::cout << "测试图像已保存为 test_output.png" << std::endl;
    return 0;
}
```

### 编译测试

#### Windows (MSVC)

```batch
# 使用 cl 编译器
cl test_opencv.cpp /I"C:\opencv\build\include" /link "C:\opencv\build\x64\vc15\lib\opencv_world450.lib"
```

#### Linux/macOS (g++)

```bash
# 使用 g++ 编译器
g++ test_opencv.cpp -o test_opencv `pkg-config --cflags --libs opencv4`
```

#### 使用 CMake

```cmake
cmake_minimum_required(VERSION 3.10)
project(test_opencv)

find_package(OpenCV REQUIRED)
add_executable(test_opencv test_opencv.cpp)
target_link_libraries(test_opencv ${OpenCV_LIBS})
```

## 常见问题解决

### 1. 找不到 OpenCV 库

**问题**：编译时出现 "cannot find -lopencv_core" 错误

**解决方案**：
```bash
# 检查 pkg-config 配置
pkg-config --libs opencv4

# 手动指定库路径
g++ test.cpp -I/usr/local/include/opencv4 -L/usr/local/lib -lopencv_core -lopencv_imgproc
```

### 2. 运行时库找不到

**问题**：程序运行时提示 "libopencv_core.so.4.5: cannot open shared object file"

**解决方案**：
```bash
# 添加库路径到 LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# 或者将库路径添加到 /etc/ld.so.conf 并运行 ldconfig
echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf
sudo ldconfig
```

### 3. 版本冲突

**问题**：系统中有多个版本的 OpenCV

**解决方案**：
```bash
# 检查已安装的版本
pkg-config --list-all | grep opencv

# 使用特定版本
pkg-config --cflags --libs opencv4
```

### 4. 缺少 contrib 模块

**问题**：使用 SIFT、SURF 等算法时出现错误

**解决方案**：
```bash
# 重新编译时包含 contrib 模块
cmake -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules ..
```

## 性能优化

### 1. 启用优化编译

```cmake
# 在 CMakeLists.txt 中添加
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native")
```

### 2. 启用并行处理

```cmake
# 启用 TBB 支持
find_package(TBB REQUIRED)
target_link_libraries(your_target ${TBB_LIBRARIES})
```

### 3. 使用 Intel IPP

```cmake
# 启用 IPP 加速
cmake -D WITH_IPP=ON ..
```

## 更新和卸载

### 更新 OpenCV

```bash
# 从源码更新
cd opencv
git pull
cd build
make clean
make -j4
sudo make install
```

### 卸载 OpenCV

```bash
# 如果使用 make install 安装
cd build
sudo make uninstall

# 手动删除文件
sudo rm -rf /usr/local/include/opencv4
sudo rm -rf /usr/local/lib/libopencv_*
sudo rm -rf /usr/local/share/opencv4
```

## 参考资料

- [OpenCV 官方文档](https://docs.opencv.org/)
- [OpenCV GitHub 仓库](https://github.com/opencv/opencv)
- [OpenCV 安装指南](https://docs.opencv.org/master/d7/d9f/tutorial_linux_install.html)