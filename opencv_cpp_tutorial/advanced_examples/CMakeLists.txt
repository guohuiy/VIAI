cmake_minimum_required(VERSION 3.10)

# 设置项目名称和版本
project(OpenCVAdvancedExamples VERSION 1.0.0)

# 设置C++标准
set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找OpenCV包
find_package(OpenCV REQUIRED)

# 创建可执行文件
add_executable(face_detection face_detection.cpp)
add_executable(video_processing video_processing.cpp)
add_executable(feature_detection feature_detection.cpp)
add_executable(image_filtering image_filtering.cpp)

# 链接OpenCV库
target_link_libraries(face_detection ${OpenCV_LIBS})
target_link_libraries(video_processing ${OpenCV_LIBS})
target_link_libraries(feature_detection ${OpenCV_LIBS})
target_link_libraries(image_filtering ${OpenCV_LIBS})

# 设置包含目录
target_include_directories(face_detection PRIVATE ${OpenCV_INCLUDE_DIRS})
target_include_directories(video_processing PRIVATE ${OpenCV_INCLUDE_DIRS})
target_include_directories(feature_detection PRIVATE ${OpenCV_INCLUDE_DIRS})
target_include_directories(image_filtering PRIVATE ${OpenCV_INCLUDE_DIRS})

# 设置编译选项
if(MSVC)
    target_compile_options(face_detection PRIVATE /W4)
    target_compile_options(video_processing PRIVATE /W4)
    target_compile_options(feature_detection PRIVATE /W4)
    target_compile_options(image_filtering PRIVATE /W4)
else()
    target_compile_options(face_detection PRIVATE -Wall -Wextra)
    target_compile_options(video_processing PRIVATE -Wall -Wextra)
    target_compile_options(feature_detection PRIVATE -Wall -Wextra)
    target_compile_options(image_filtering PRIVATE -Wall -Wextra)
endif()

# 安装目标
install(TARGETS face_detection video_processing feature_detection image_filtering DESTINATION bin)