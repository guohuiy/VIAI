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

# 设置编译选项
if(MSVC)
    target_compile_options(opencv_example PRIVATE /W4)
else()
    target_compile_options(opencv_example PRIVATE -Wall -Wextra)
endif()

# 安装目标
install(TARGETS opencv_example DESTINATION bin)