# OpenCV C++ 项目构建指南

## 项目结构

```
opencv_cpp_tutorial/
├── CMakeLists.txt              # 主项目配置
├── main.cpp                    # 基础示例
├── README.md                   # 项目说明
├── opencv_install_guide.md     # OpenCV安装指南
├── build_instructions.md       # 本文件
└── advanced_examples/          # 高级示例
    ├── CMakeLists.txt          # 高级示例配置
    ├── face_detection.cpp      # 人脸检测
    ├── video_processing.cpp    # 视频处理
    ├── feature_detection.cpp   # 特征检测
    └── image_filtering.cpp     # 图像滤波
```

## 构建步骤

### 1. 安装 OpenCV

在开始构建项目之前，请确保已正确安装 OpenCV。详细安装步骤请参考 `opencv_install_guide.md`。

### 2. 使用 CMake 构建

#### Windows 平台

```batch
# 打开命令提示符或 PowerShell
cd opencv_cpp_tutorial

# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译项目
cmake --build . --config Release

# 运行示例程序
.\Release\opencv_example.exe
```

#### Linux/macOS 平台

```bash
# 打开终端
cd opencv_cpp_tutorial

# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译项目
make

# 运行示例程序
./opencv_example
```

### 3. 构建高级示例

高级示例位于 `advanced_examples` 目录中，需要单独构建：

```bash
# 进入高级示例目录
cd advanced_examples

# 创建构建目录
mkdir build
cd build

# 配置项目
cmake ..

# 编译所有示例
make

# 运行特定示例
./face_detection
./video_processing
./feature_detection
./image_filtering
```

## 构建选项

### CMake 选项

```bash
# 指定构建类型
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake -DCMAKE_BUILD_TYPE=Debug ..

# 指定安装路径
cmake -DCMAKE_INSTALL_PREFIX=/usr/local ..

# 启用特定功能
cmake -DWITH_TBB=ON -DWITH_IPP=ON ..
```

### 编译器选项

#### GCC/Clang

```bash
# 设置编译器
export CC=gcc
export CXX=g++

# 添加编译选项
cmake -DCMAKE_CXX_FLAGS="-O3 -march=native" ..
```

#### MSVC

```batch
# 使用特定版本的 Visual Studio
cmake -G "Visual Studio 16 2019" -A x64 ..

# 设置编译器选项
cmake -DCMAKE_CXX_FLAGS="/W4 /O2" ..
```

## 常见构建问题

### 1. 找不到 OpenCV

**错误信息**：
```
CMake Error at CMakeLists.txt:10 (find_package):
  By not providing "FindOpenCV.cmake" in CMAKE_MODULE_PATH this project has
  asked CMake to find a package configuration file provided by "OpenCV", but
  CMake did not find one.
```

**解决方案**：
```bash
# 设置 OpenCV_DIR 环境变量
export OpenCV_DIR=/usr/local/share/opencv4  # Linux/macOS
set OpenCV_DIR=C:\opencv\build  # Windows
```

### 2. 链接错误

**错误信息**：
```
undefined reference to `cv::imread(cv::String const&, int)'
```

**解决方案**：
```bash
# 检查 pkg-config 配置
pkg-config --libs opencv4

# 手动指定库路径
cmake -DOpenCV_LIBS="-lopencv_core -lopencv_imgproc -lopencv_highgui" ..
```

### 3. 版本不匹配

**错误信息**：
```
error: ‘CV_VERSION’ was not declared in this scope
```

**解决方案**：
```cpp
// 使用新的版本宏
#include <opencv2/core/version.hpp>
std::cout << CV_VERSION << std::endl;

// 或者使用字符串版本
std::cout << CV_VERSION_STR << std::endl;
```

## 性能优化

### 1. 启用优化编译

```cmake
# 在 CMakeLists.txt 中添加
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -march=native")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -g")
```

### 2. 启用并行编译

```bash
# 使用多线程编译
make -j4  # 使用4个线程
cmake --build . --parallel 4  # CMake 3.12+
```

### 3. 启用 SIMD 优化

```cmake
# 启用 SSE/AVX 优化
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -msse4.2 -mavx2")
```

## 调试技巧

### 1. 启用调试信息

```cmake
# 设置调试模式
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -DDEBUG")
```

### 2. 使用 Valgrind 检测内存问题（Linux）

```bash
# 编译时包含调试信息
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 运行 Valgrind
valgrind --leak-check=full ./opencv_example
```

### 3. 使用 GDB 调试

```bash
# 编译调试版本
cmake -DCMAKE_BUILD_TYPE=Debug ..
make

# 使用 GDB 调试
gdb ./opencv_example
```

## 部署说明

### 1. 静态链接

```cmake
# 启用静态链接
set(BUILD_SHARED_LIBS OFF)
find_package(OpenCV REQUIRED)
```

### 2. 创建安装包

```bash
# 安装到指定目录
make install DESTDIR=./install

# 创建压缩包
tar -czf opencv_example.tar.gz install/
```

### 3. 跨平台部署

```bash
# 使用交叉编译工具链
cmake -DCMAKE_TOOLCHAIN_FILE=toolchain.cmake ..
```

## 测试

### 1. 运行基础测试

```bash
# 编译并运行基础示例
cd build
make
./opencv_example
```

### 2. 运行高级示例

```bash
# 编译高级示例
cd advanced_examples/build
make

# 运行各个示例
./face_detection
./video_processing
./feature_detection
./image_filtering
```

### 3. 性能测试

```cpp
// 在代码中添加性能测试
auto start = std::chrono::high_resolution_clock::now();

// OpenCV 操作
cv::Mat result;
cv::GaussianBlur(image, result, cv::Size(15, 15), 0);

auto end = std::chrono::high_resolution_clock::now();
auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
std::cout << "处理时间: " << duration.count() << " ms" << std::endl;
```

## 故障排除

### 1. 清理构建

```bash
# 清理构建目录
rm -rf build
mkdir build
cd build
cmake ..
make
```

### 2. 检查 OpenCV 安装

```bash
# 检查 OpenCV 版本
pkg-config --modversion opencv4

# 检查 OpenCV 库
pkg-config --libs opencv4

# 检查 OpenCV 头文件
pkg-config --cflags opencv4
```

### 3. 更新 OpenCV

```bash
# 从源码更新
cd opencv
git pull
cd build
make clean
make -j4
sudo make install
```

## 参考资料

- [CMake 官方文档](https://cmake.org/documentation/)
- [OpenCV C++ API](https://docs.opencv.org/master/)
- [CMake OpenCV 示例](https://github.com/opencv/opencv/tree/master/samples/cpp)