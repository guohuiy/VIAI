# OpenCV C++ 项目部署教程

本教程将指导你如何在C++项目中部署和使用OpenCV库。

## 目录

1. [OpenCV安装](#opencv安装)
2. [项目配置](#项目配置)
3. [编译和运行](#编译和运行)
4. [代码示例](#代码示例)
5. [常见问题](#常见问题)

## OpenCV安装

### Windows平台

#### 方法1：使用预编译库（推荐）

1. **下载OpenCV预编译库**
   - 访问 [OpenCV官网下载页面](https://opencv.org/releases/)
   - 下载适合你系统的预编译版本（Windows版）

2. **解压和配置环境变量**
   ```bash
   # 解压到 C:\opencv
   # 添加环境变量
   OPENCV_DIR=C:\opencv\build\x64\vc15
   PATH=%PATH%;%OPENCV_DIR%\bin
   ```

3. **验证安装**
   ```bash
   # 检查环境变量
   echo %OPENCV_DIR%
   ```

#### 方法2：从源码编译

1. **安装CMake**
   - 下载并安装 [CMake](https://cmake.org/download/)

2. **下载OpenCV源码**
   ```bash
   git clone https://github.com/opencv/opencv.git
   git clone https://github.com/opencv/opencv_contrib.git
   ```

3. **编译OpenCV**
   ```bash
   cd opencv
   mkdir build
   cd build
   cmake -D CMAKE_BUILD_TYPE=Release \
         -D CMAKE_INSTALL_PREFIX=C:\opencv \
         -D OPENCV_EXTRA_MODULES_PATH=..\..\opencv_contrib\modules \
         ..
   cmake --build . --config Release --target install
   ```

### Linux平台

#### Ubuntu/Debian

```bash
# 更新包管理器
sudo apt update

# 安装依赖
sudo apt install build-essential cmake pkg-config
sudo apt install libjpeg-dev libtiff5-dev libpng-dev
sudo apt install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install libxvidcore-dev libx264-dev
sudo apt install libfontconfig1-dev libcairo2-dev
sudo apt install libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt install libgtk2.0-dev libgtk-3-dev
sudo apt install libatlas-base-dev gfortran
sudo apt install python3-dev python3-numpy

# 下载OpenCV
wget -O opencv.zip https://github.com/opencv/opencv/archive/4.x.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/4.x.zip

# 解压
unzip opencv.zip
unzip opencv_contrib.zip

# 编译安装
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

#### CentOS/RHEL

```bash
# 安装EPEL仓库
sudo yum install epel-release
sudo yum update

# 安装依赖
sudo yum install gcc gcc-c++ cmake3
sudo yum install gtk2-devel libpng-devel
sudo yum install jasper-devel openexr-devel libwebp-devel
sudo yum install libjpeg-turbo-devel libtiff-devel
sudo yum install tbb-devel eigen3-devel

# 编译安装（类似Ubuntu步骤）
```

### macOS平台

#### 使用Homebrew

```bash
# 安装Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装OpenCV
brew install opencv

# 验证安装
pkg-config --modversion opencv4
```

#### 使用MacPorts

```bash
# 安装OpenCV
sudo port install opencv4

# 验证安装
pkg-config --modversion opencv4
```

## 项目配置

### 使用CMake（推荐）

创建 `CMakeLists.txt` 文件：

```cmake
cmake_minimum_required(VERSION 3.10)

# 设置项目名称和版本
project(OpenCVCppTutorial VERSION 1.0.0)

# 设置C++标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找OpenCV包
find_package(OpenCV REQUIRED)

# 创建可执行文件
add_executable(opencv_example main.cpp)

# 链接OpenCV库
target_link_libraries(opencv_example ${OpenCV_LIBS})

# 设置包含目录
target_include_directories(opencv_example PRIVATE ${OpenCV_INCLUDE_DIRS})
```

### 使用Makefile

```makefile
CXX = g++
CXXFLAGS = -std=c++14 -Wall -Wextra
OPENCV_CFLAGS = $(shell pkg-config --cflags opencv4)
OPENCV_LIBS = $(shell pkg-config --libs opencv4)

TARGET = opencv_example
SOURCES = main.cpp

$(TARGET): $(SOURCES)
	$(CXX) $(CXXFLAGS) $(OPENCV_CFLAGS) -o $(TARGET) $(SOURCES) $(OPENCV_LIBS)

clean:
	rm -f $(TARGET)

.PHONY: clean
```

### Visual Studio配置

1. **创建新项目**
   - 打开Visual Studio
   - 创建新的C++控制台应用程序

2. **配置项目属性**
   - 右键项目 → 属性
   - C/C++ → 常规 → 附加包含目录
     ```
     C:\opencv\build\include
     C:\opencv\build\include\opencv2
     ```
   - 链接器 → 常规 → 附加库目录
     ```
     C:\opencv\build\x64\vc15\lib
     ```
   - 链接器 → 输入 → 附加依赖项
     ```
     opencv_world450.lib
     ```

## 编译和运行

### 使用CMake

```bash
# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译项目
cmake --build .

# 运行程序
./opencv_example
```

### 使用Makefile

```bash
# 编译
make

# 运行
./opencv_example
```

### 使用Visual Studio

1. 按 F5 或点击"启动调试"
2. 程序将在控制台中运行

## 代码示例

### 基础图像处理

```cpp
#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // 读取图像
    cv::Mat image = cv::imread("input.jpg");
    
    if (image.empty()) {
        std::cout << "无法读取图像文件" << std::endl;
        return -1;
    }
    
    // 转换为灰度图像
    cv::Mat gray;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
    
    // 显示图像
    cv::imshow("原始图像", image);
    cv::imshow("灰度图像", gray);
    cv::waitKey(0);
    
    return 0;
}
```

### 视频处理

```cpp
#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // 打开摄像头
    cv::VideoCapture cap(0);
    
    if (!cap.isOpened()) {
        std::cout << "无法打开摄像头" << std::endl;
        return -1;
    }
    
    cv::Mat frame;
    
    while (true) {
        // 读取帧
        cap >> frame;
        
        if (frame.empty()) break;
        
        // 显示帧
        cv::imshow("摄像头", frame);
        
        // 按ESC键退出
        if (cv::waitKey(30) == 27) break;
    }
    
    cap.release();
    cv::destroyAllWindows();
    
    return 0;
}
```

### 特征检测

```cpp
#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>
#include <iostream>

int main() {
    // 读取图像
    cv::Mat image = cv::imread("input.jpg");
    
    // 创建ORB特征检测器
    cv::Ptr<cv::ORB> orb = cv::ORB::create();
    
    // 检测关键点
    std::vector<cv::KeyPoint> keypoints;
    cv::Mat descriptors;
    orb->detectAndCompute(image, cv::noArray(), keypoints, descriptors);
    
    // 绘制关键点
    cv::Mat output;
    cv::drawKeypoints(image, keypoints, output, cv::Scalar::all(-1), 
                     cv::DrawMatchesFlags::DEFAULT);
    
    // 显示结果
    cv::imshow("特征检测", output);
    cv::waitKey(0);
    
    return 0;
}
```

## 常见问题

### 1. 找不到OpenCV库

**问题**：编译时出现"找不到OpenCV"错误

**解决方案**：
- 检查OpenCV是否正确安装
- 验证环境变量设置
- 确认CMakeLists.txt中的find_package路径正确

### 2. 链接错误

**问题**：链接时出现未定义引用错误

**解决方案**：
- 确保链接了正确的OpenCV库
- 检查库版本兼容性
- 确认编译器和OpenCV版本匹配

### 3. 运行时错误

**问题**：程序运行时崩溃或无法加载库

**解决方案**：
- 确保运行时库路径正确
- 检查DLL文件是否在PATH中
- 验证OpenCV版本与项目兼容

### 4. 性能问题

**问题**：程序运行缓慢

**解决方案**：
- 使用Release模式编译
- 启用优化选项
- 考虑使用多线程处理

## 进一步学习

- [OpenCV官方文档](https://docs.opencv.org/)
- [OpenCV C++教程](https://docs.opencv.org/master/d9/df8/tutorial_root.html)
- [OpenCV GitHub仓库](https://github.com/opencv/opencv)

## 许可证

本教程遵循MIT许可证。OpenCV库遵循BSD 3-Clause许可证。