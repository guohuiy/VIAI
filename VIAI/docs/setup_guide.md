# VIAI 运行环境搭建指南

## 环境要求

### 操作系统
- **Windows 10/11** (推荐)
- Linux (Ubuntu 20.04+)
- macOS (可选)

### 硬件要求
- **CPU**: Intel/AMD 64位处理器，支持AVX2指令集
- **内存**: 16GB RAM (推荐32GB+)
- **GPU**: NVIDIA GPU (推荐RTX 1080 Ti或更高)
  - 支持CUDA 11.8+
  - 显存4GB+ (推荐8GB+)
- **存储**: 50GB可用空间

### 软件依赖

#### 必需依赖
1. **CMake 3.20+**
   - 下载地址: https://cmake.org/download/
   - 验证安装: `cmake --version`

2. **C++ 编译器**
   - **Windows**: Visual Studio 2022 (Community版免费)
     - 安装C++桌面开发工作负载
     - 确保包含MSVC编译器
   - **Linux**: GCC 9.3+ 或 Clang 10+
     - Ubuntu: `sudo apt install build-essential`

3. **Git**
   - 下载地址: https://git-scm.com/downloads

#### 推荐依赖

4. **OpenCV 4.8+**
   - 下载地址: https://opencv.org/releases/
   - Windows: 下载预编译版本或源码编译
   - Linux: `sudo apt install libopencv-dev`

5. **CUDA Toolkit 11.8+** (GPU加速必需)
   - 下载地址: https://developer.nvidia.com/cuda-downloads
   - 验证安装: `nvcc --version`

6. **cuDNN 8.6+** (深度学习加速)
   - 下载地址: https://developer.nvidia.com/cudnn
   - 需要NVIDIA开发者账号

#### 可选依赖 (推理引擎)

7. **TensorRT 8.6+** (NVIDIA推荐)
   - 下载地址: https://developer.nvidia.com/tensorrt
   - 需要NVIDIA开发者账号

8. **ONNX Runtime 1.15+**
   - 下载地址: https://github.com/microsoft/onnxruntime/releases
   - 支持CPU/GPU加速

9. **OpenVINO 2023.0+** (Intel CPU优化)
   - 下载地址: https://www.intel.com/content/www/us/en/developer/tools/openvino-toolkit/overview.html

10. **NCNN** (移动端优化)
    - GitHub: https://github.com/Tencent/ncnn
    - 适用于轻量级部署

## Windows 环境搭建步骤

### 1. 安装 Visual Studio 2022
1. 下载 Visual Studio 2022 Community
2. 运行安装程序
3. 选择"使用C++的桌面开发"工作负载
4. 确保包含以下组件:
   - MSVC v143 编译器工具集
   - Windows 10/11 SDK
   - CMake 工具

### 2. 安装 CMake
1. 下载 CMake Windows installer
2. 运行安装程序
3. 选择"Add CMake to the system PATH for all users"
4. 验证安装:
   ```cmd
   cmake --version
   ```

### 3. 安装 CUDA Toolkit
1. 下载 CUDA 11.8+ Windows installer
2. 运行安装程序，选择"自定义安装"
3. 确保安装:
   - CUDA Tools
   - CUDA Runtime
   - Visual Studio Integration
4. 验证安装:
   ```cmd
   nvcc --version
   ```

### 4. 安装 cuDNN
1. 下载 cuDNN for CUDA 11.8+
2. 解压到 CUDA 安装目录 (通常是 `C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8`)
3. 复制文件:
   - `bin\` → `CUDA\v11.8\bin\`
   - `include\` → `CUDA\v11.8\include\`
   - `lib\` → `CUDA\v11.8\lib\`

### 5. 安装 OpenCV
**方法1: 预编译版本**
1. 下载 OpenCV 4.8+ Windows预编译包
2. 解压到 `C:\opencv\`
3. 设置环境变量:
   - `OPENCV_DIR=C:\opencv\build`
   - `PATH` 添加 `C:\opencv\build\x64\vc16\bin`

**方法2: 源码编译**
```cmd
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=C:\opencv ..
cmake --build . --config Release --target install
```

### 6. 安装推理引擎 (可选)

#### TensorRT 安装
1. 下载 TensorRT 8.6+ for Windows
2. 解压到 `C:\tensorrt\`
3. 设置环境变量:
   - `TENSORRT_DIR=C:\tensorrt\`
   - `PATH` 添加 `C:\tensorrt\lib`

#### ONNX Runtime 安装
1. 下载 ONNX Runtime for Windows
2. 解压到 `C:\onnxruntime\`
3. 设置环境变量:
   - `ONNXRUNTIME_DIR=C:\onnxruntime\`

## Linux 环境搭建步骤 (Ubuntu 20.04+)

### 1. 更新系统
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. 安装基础工具
```bash
sudo apt install -y build-essential cmake git wget unzip
```

### 3. 安装 CUDA (如果使用NVIDIA GPU)
```bash
# 添加 NVIDIA 仓库
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2004-11-8-local_11.8.89-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-8-local_11.8.89-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2004-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

### 4. 安装 cuDNN
```bash
# 下载 cuDNN (需要注册NVIDIA开发者账号)
# 解压并复制文件到CUDA目录
sudo cp cuda/include/cudnn*.h /usr/local/cuda/include
sudo cp cuda/lib64/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```

### 5. 安装 OpenCV
```bash
# 方法1: 使用包管理器
sudo apt install -y libopencv-dev python3-opencv

# 方法2: 源码编译
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local ..
make -j$(nproc)
sudo make install
```

### 6. 设置环境变量
```bash
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## 验证环境

### 检查编译器
```cmd
# Windows
cl.exe

# Linux
g++ --version
```

### 检查 CMake
```cmd
cmake --version
```

### 检查 CUDA (如果安装)
```cmd
nvcc --version
nvidia-smi
```

### 检查 OpenCV
```cpp
// 创建测试文件 test_opencv.cpp
#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    cv::Mat img = cv::Mat::zeros(100, 100, CV_8UC3);
    std::cout << "OpenCV version: " << CV_VERSION << std::endl;
    std::cout << "Test image size: " << img.rows << "x" << img.cols << std::endl;
    return 0;
}
```

编译测试:
```cmd
# Windows
g++ -I"C:\opencv\build\include" -L"C:\opencv\build\x64\vc16\lib" -lopencv_core480 -lopencv_imgproc480 test_opencv.cpp -o test_opencv

# Linux
g++ -I/usr/local/include/opencv4 -L/usr/local/lib -lopencv_core -lopencv_imgproc test_opencv.cpp -o test_opencv
```

## 项目构建

### 1. 克隆项目
```cmd
cd D:\windows\桌面
git clone <repository-url> VIAI
cd VIAI
```

### 2. 创建构建目录
```cmd
mkdir build
cd build
```

### 3. 配置 CMake
```cmd
# Windows
cmake -DCMAKE_BUILD_TYPE=Release -G "Visual Studio 17 2022" -A x64 ..

# Linux
cmake -DCMAKE_BUILD_TYPE=Release ..
```

### 4. 编译项目
```cmd
# Windows
cmake --build . --config Release --parallel

# Linux
make -j$(nproc)
```

### 5. 运行测试
```cmd
# 运行主程序
./viai

# 运行单元测试
./viai_tests
```

## 常见问题解决

### 1. CMake 找不到包
- 确保环境变量设置正确
- 检查包的安装路径
- 使用 `find_package()` 的 `REQUIRED` 选项查看详细错误

### 2. 编译错误
- 检查编译器版本兼容性
- 确保所有依赖已正确安装
- 查看具体的错误信息

### 3. 运行时错误
- 检查动态库路径
- 确保CUDA驱动版本兼容
- 验证GPU是否被正确识别

### 4. 性能问题
- 确保使用Release模式编译
- 检查是否启用了GPU加速
- 验证内存分配是否合理

## 性能优化建议

### 编译优化
```cmd
# 启用高级优化
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-O3 -march=native -flto" ..

# 启用链接时优化 (Linux)
cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INTERPROCEDURAL_OPTIMIZATION=ON ..
```

### 运行时优化
1. **GPU 内存优化**: 根据显存大小调整批处理大小
2. **多线程**: 启用多线程推理
3. **混合精度**: 使用FP16/INT8量化
4. **模型优化**: 使用TensorRT优化模型

## 下一步

环境搭建完成后，可以:
1. 运行示例程序测试基本功能
2. 开发自定义插件
3. 集成具体的AI模型
4. 进行性能调优

如有问题，请参考项目文档或提交Issue。