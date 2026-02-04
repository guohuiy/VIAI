# VIAI 依赖项清单

## 核心依赖项

### 必需依赖项

| 依赖项 | 版本要求 | 用途 | 安装方式 |
|--------|----------|------|----------|
| CMake | 3.20+ | 构建系统 | 官网下载 |
| C++ 编译器 | C++17支持 | 代码编译 | VS2022/GCC9+/Clang10+ |
| Git | 任意 | 版本控制 | 官网下载 |

### 推荐依赖项

| 依赖项 | 版本要求 | 用途 | 安装方式 |
|--------|----------|------|----------|
| OpenCV | 4.8+ | 计算机视觉处理 | 预编译包/源码编译 |
| CUDA Toolkit | 11.8+ | GPU加速 | NVIDIA官网 |
| cuDNN | 8.6+ | 深度学习加速 | NVIDIA开发者网站 |

### 可选依赖项 (推理引擎)

| 依赖项 | 版本要求 | 用途 | 安装方式 |
|--------|----------|------|----------|
| TensorRT | 8.6+ | NVIDIA推理优化 | NVIDIA开发者网站 |
| ONNX Runtime | 1.15+ | 跨平台推理 | GitHub releases |
| OpenVINO | 2023.0+ | Intel CPU优化 | Intel官网 |
| NCNN | 最新 | 轻量级推理 | GitHub源码 |

## 详细安装指南

### Windows 10/11

#### 1. Visual Studio 2022 Community
```powershell
# 下载并安装
Invoke-WebRequest -Uri "https://aka.ms/vs/17/release/vs_community.exe" -OutFile "vs_community.exe"
.\vs_community.exe

# 安装时选择组件:
# - 使用C++的桌面开发
# - Windows 10/11 SDK
# - CMake工具
```

#### 2. CMake
```powershell
# 下载安装包
Invoke-WebRequest -Uri "https://github.com/Kitware/CMake/releases/download/v3.28.0/cmake-3.28.0-windows-x86_64.msi" -OutFile "cmake.msi"
msiexec /i cmake.msi /quiet ADD_CMAKE_TO_PATH=System

# 验证安装
cmake --version
```

#### 3. CUDA Toolkit 11.8
```powershell
# 下载CUDA 11.8
Invoke-WebRequest -Uri "https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda_11.8.0_522.06_windows.exe" -OutFile "cuda_11.8.exe"
.\cuda_11.8.exe

# 验证安装
nvcc --version
nvidia-smi
```

#### 4. cuDNN 8.6
```powershell
# 需要注册NVIDIA开发者账号
# 下载cuDNN for CUDA 11.8
# 解压到CUDA安装目录
Expand-Archive -Path "cudnn-windows-x86_64-8.6.0.163_cuda11.8-archive.zip" -DestinationPath "C:\cuda\"

# 复制文件
Copy-Item "C:\cuda\bin\*" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin\" -Force
Copy-Item "C:\cuda\include\*" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\include\" -Force
Copy-Item "C:\cuda\lib\*" "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\lib\vc\*" -Force
```

#### 5. OpenCV 4.8
```powershell
# 下载预编译版本
Invoke-WebRequest -Uri "https://github.com/opencv/opencv/releases/download/4.8.0/opencv-4.8.0-vc14_vc15.x86_64.exe" -OutFile "opencv.exe"
.\opencv.exe

# 设置环境变量
[Environment]::SetEnvironmentVariable("OPENCV_DIR", "C:\opencv\build", "Machine")
[Environment]::SetEnvironmentVariable("PATH", "$env:PATH;C:\opencv\build\x64\vc16\bin", "Machine")
```

### Linux (Ubuntu 20.04+)

#### 1. 基础工具
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础工具
sudo apt install -y build-essential cmake git wget unzip curl

# 安装Python3和pip
sudo apt install -y python3 python3-pip
```

#### 2. CUDA Toolkit
```bash
# 添加NVIDIA仓库
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
sudo mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600

# 下载并安装CUDA
wget https://developer.download.nvidia.com/compute/cuda/11.8.0/local_installers/cuda-repo-ubuntu2004-11-8-local_11.8.89-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu2004-11-8-local_11.8.89-1_amd64.deb
sudo cp /var/cuda-repo-ubuntu2004-11-8-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda

# 设置环境变量
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

#### 3. cuDNN
```bash
# 下载cuDNN (需要NVIDIA开发者账号)
# 注册地址: https://developer.nvidia.com/cudnn

# 解压并安装
tar -xvf cudnn-linux-x86_64-8.6.0.163_cuda11.8-archive.tar.xz
sudo cp cudnn-*-archive/include/cudnn*.h /usr/local/cuda/include
sudo cp -P cudnn-*-archive/lib/libcudnn* /usr/local/cuda/lib64
sudo chmod a+r /usr/local/cuda/include/cudnn*.h /usr/local/cuda/lib64/libcudnn*
```

#### 4. OpenCV
```bash
# 方法1: 使用包管理器 (推荐)
sudo apt install -y libopencv-dev python3-opencv

# 方法2: 源码编译
git clone https://github.com/opencv/opencv.git
cd opencv
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/usr/local \
      -DWITH_CUDA=ON \
      -DWITH_CUDNN=ON \
      -DOPENCV_DNN_CUDA=ON \
      -DCUDA_ARCH_BIN=7.5 \
      -DWITH_CUBLAS=ON \
      -DWITH_TBB=ON \
      -DWITH_V4L=ON \
      -DWITH_QT=ON \
      -DWITH_OPENGL=ON \
      -DBUILD_EXAMPLES=ON ..
make -j$(nproc)
sudo make install
```

#### 5. 推理引擎

##### TensorRT
```bash
# 下载TensorRT
wget https://developer.download.nvidia.com/compute/machine-learning/tensorrt/secure/8.6.0/jax_cuda_11.8/tensorrt-8.6.0.12.linux.x86_64-gnu.cuda-11.8.cudnn8.6.tar.gz

# 解压
tar -xzf tensorrt-8.6.0.12.linux.x86_64-gnu.cuda-11.8.cudnn8.6.tar.gz

# 设置环境变量
echo 'export TENSORRT_DIR=/path/to/TensorRT-8.6.0.12' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$TENSORRT_DIR/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

##### ONNX Runtime
```bash
# 下载ONNX Runtime
wget https://github.com/microsoft/onnxruntime/releases/download/v1.15.1/onnxruntime-linux-x64-1.15.1.tgz

# 解压
tar -xzf onnxruntime-linux-x64-1.15.1.tgz

# 设置环境变量
echo 'export ONNXRUNTIME_DIR=/path/to/onnxruntime-linux-x64-1.15.1' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=$ONNXRUNTIME_DIR/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc
```

## 验证安装

### 创建验证脚本

#### Windows (verify_env.bat)
```batch
@echo off
echo === VIAI 环境验证 ===
echo.

echo 1. 检查编译器...
cl.exe >nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Visual Studio 编译器可用
) else (
    echo ✗ Visual Studio 编译器不可用
)

echo.
echo 2. 检查CMake...
cmake --version
if %errorlevel% == 0 (
    echo ✓ CMake 可用
) else (
    echo ✗ CMake 不可用
)

echo.
echo 3. 检查CUDA...
nvcc --version
if %errorlevel% == 0 (
    echo ✓ CUDA 编译器可用
) else (
    echo ✗ CUDA 编译器不可用
)

nvidia-smi
if %errorlevel% == 0 (
    echo ✓ NVIDIA 驱动可用
) else (
    echo ✗ NVIDIA 驱动不可用
)

echo.
echo 4. 检查OpenCV...
python -c "import cv2; print('OpenCV version:', cv2.__version__)"
if %errorlevel% == 0 (
    echo ✓ OpenCV Python 可用
) else (
    echo ✗ OpenCV Python 不可用
)

echo.
echo 环境验证完成！
pause
```

#### Linux (verify_env.sh)
```bash
#!/bin/bash
echo "=== VIAI 环境验证 ==="
echo

echo "1. 检查编译器..."
g++ --version
if [ $? -eq 0 ]; then
    echo "✓ GCC 编译器可用"
else
    echo "✗ GCC 编译器不可用"
fi

echo
echo "2. 检查CMake..."
cmake --version
if [ $? -eq 0 ]; then
    echo "✓ CMake 可用"
else
    echo "✗ CMake 不可用"
fi

echo
echo "3. 检查CUDA..."
nvcc --version
if [ $? -eq 0 ]; then
    echo "✓ CUDA 编译器可用"
else
    echo "✗ CUDA 编译器不可用"
fi

nvidia-smi
if [ $? -eq 0 ]; then
    echo "✓ NVIDIA 驱动可用"
else
    echo "✗ NVIDIA 驱动不可用"
fi

echo
echo "4. 检查OpenCV..."
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
if [ $? -eq 0 ]; then
    echo "✓ OpenCV Python 可用"
else
    echo "✗ OpenCV Python 不可用"
fi

echo
echo "环境验证完成！"
```

### 运行验证
```bash
# Windows
verify_env.bat

# Linux
chmod +x verify_env.sh
./verify_env.sh
```

## 性能基准测试

### 创建基准测试脚本

#### test_performance.cpp
```cpp
#include <iostream>
#include <chrono>
#include <vector>
#include <opencv2/opencv.hpp>

#ifdef __CUDACC__
#include <cuda_runtime.h>
#include <cuda_runtime_api.h>
#endif

int main() {
    std::cout << "=== VIAI 性能基准测试 ===" << std::endl;
    
    // 1. CPU 性能测试
    std::cout << "\n1. CPU 性能测试:" << std::endl;
    cv::Mat cpu_img(1080, 1920, CV_8UC3, cv::Scalar(255, 255, 255));
    auto start = std::chrono::high_resolution_clock::now();
    
    for (int i = 0; i < 100; ++i) {
        cv::GaussianBlur(cpu_img, cpu_img, cv::Size(5, 5), 0);
    }
    
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);
    std::cout << "   CPU 高斯模糊 (100次): " << duration.count() << "ms" << std::endl;
    
    // 2. GPU 性能测试 (如果可用)
#ifdef __CUDACC__
    std::cout << "\n2. GPU 性能测试:" << std::endl;
    
    int deviceCount;
    cudaGetDeviceCount(&deviceCount);
    if (deviceCount > 0) {
        cudaDeviceProp prop;
        cudaGetDeviceProperties(&prop, 0);
        std::cout << "   GPU: " << prop.name << std::endl;
        std::cout << "   显存: " << prop.totalGlobalMem / (1024 * 1024) << "MB" << std::endl;
        std::cout << "   CUDA 核心: " << prop.multiProcessorCount * 128 << std::endl;
        
        // GPU 内存分配测试
        float* d_data;
        size_t size = 1024 * 1024 * 100; // 100MB
        auto gpu_start = std::chrono::high_resolution_clock::now();
        
        cudaMalloc(&d_data, size);
        cudaMemset(d_data, 0, size);
        cudaFree(d_data);
        
        auto gpu_end = std::chrono::high_resolution_clock::now();
        auto gpu_duration = std::chrono::duration_cast<std::chrono::milliseconds>(gpu_end - gpu_start);
        std::cout << "   GPU 内存操作: " << gpu_duration.count() << "ms" << std::endl;
    } else {
        std::cout << "   未检测到GPU" << std::endl;
    }
#endif
    
    // 3. 内存性能测试
    std::cout << "\n3. 内存性能测试:" << std::endl;
    std::vector<char> buffer(1024 * 1024 * 100); // 100MB
    auto mem_start = std::chrono::high_resolution_clock::now();
    
    for (int i = 0; i < 10; ++i) {
        std::fill(buffer.begin(), buffer.end(), i % 256);
    }
    
    auto mem_end = std::chrono::high_resolution_clock::now();
    auto mem_duration = std::chrono::duration_cast<std::chrono::milliseconds>(mem_end - mem_start);
    std::cout << "   内存填充 (1GB): " << mem_duration.count() << "ms" << std::endl;
    
    std::cout << "\n基准测试完成！" << std::endl;
    return 0;
}
```

### 编译和运行基准测试
```bash
# Windows
g++ -I"C:\opencv\build\include" -L"C:\opencv\build\x64\vc16\lib" -lopencv_core480 -lopencv_imgproc480 test_performance.cpp -o test_performance
./test_performance.exe

# Linux
g++ -I/usr/local/include/opencv4 -L/usr/local/lib -lopencv_core -lopencv_imgproc test_performance.cpp -o test_performance
./test_performance
```

## 故障排除

### 常见问题

#### 1. CMake 找不到包
```bash
# 检查包路径
echo $CMAKE_PREFIX_PATH

# 手动指定路径
cmake -DOpenCV_DIR=/path/to/opencv/build ..
```

#### 2. CUDA 编译错误
```bash
# 检查CUDA版本兼容性
nvcc --version
nvidia-smi

# 重新安装CUDA工具包
```

#### 3. OpenCV 链接错误
```bash
# 检查库文件
ls /usr/local/lib/libopencv_*.so

# 重新编译OpenCV
make clean && make -j$(nproc)
```

#### 4. 性能问题
```bash
# 检查GPU使用情况
nvidia-smi

# 检查内存使用
free -h

# 检查CPU使用
top
```

### 调试工具

#### 1. GPU 诊断
```bash
# 检查CUDA设备
nvidia-smi

# 检查CUDA版本
nvcc --version

# 运行CUDA示例
cd /usr/local/cuda/samples/1_Utilities/deviceQuery
make
./deviceQuery
```

#### 2. 内存诊断
```bash
# 检查内存使用
valgrind --tool=memcheck ./viai

# 检查内存泄漏
valgrind --tool=memcheck --leak-check=full ./viai
```

#### 3. 性能分析
```bash
# CPU 性能分析
perf record ./viai
perf report

# GPU 性能分析
nvprof ./viai
```

## 下一步

环境搭建完成后，可以:

1. **运行示例程序**: 测试基本功能
2. **开发自定义插件**: 实现特定算法
3. **集成AI模型**: 加载预训练模型
4. **性能调优**: 优化推理性能
5. **部署应用**: 容器化部署

如有问题，请参考:
- [VIAI 架构文档](architecture.md)
- [项目README](README.md)
- 提交Issue或联系开发团队