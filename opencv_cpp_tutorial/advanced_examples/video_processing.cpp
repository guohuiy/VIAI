#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // 打开视频文件或摄像头
    cv::VideoCapture cap("input_video.mp4");  // 或者使用 0 表示摄像头
    
    if (!cap.isOpened()) {
        std::cout << "无法打开视频文件或摄像头" << std::endl;
        return -1;
    }
    
    // 获取视频属性
    double fps = cap.get(cv::CAP_PROP_FPS);
    int width = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_WIDTH));
    int height = static_cast<int>(cap.get(cv::CAP_PROP_FRAME_HEIGHT));
    
    std::cout << "视频帧率: " << fps << std::endl;
    std::cout << "视频尺寸: " << width << "x" << height << std::endl;
    
    // 创建视频写入器
    cv::VideoWriter writer("output_video.avi", cv::VideoWriter::fourcc('M','J','P','G'), fps, cv::Size(width, height));
    
    cv::Mat frame, gray, edges;
    
    while (true) {
        // 读取帧
        cap >> frame;
        
        if (frame.empty()) break;
        
        // 转换为灰度图像
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        
        // 边缘检测
        cv::Canny(gray, edges, 50, 150);
        
        // 将边缘检测结果转换为三通道图像
        cv::Mat edges_3ch;
        cv::cvtColor(edges, edges_3ch, cv::COLOR_GRAY2BGR);
        
        // 显示原始视频和处理后的视频
        cv::imshow("原始视频", frame);
        cv::imshow("边缘检测", edges_3ch);
        
        // 写入处理后的帧
        writer.write(edges_3ch);
        
        // 按ESC键退出
        if (cv::waitKey(30) == 27) break;
    }
    
    // 释放资源
    cap.release();
    writer.release();
    cv::destroyAllWindows();
    
    std::cout << "视频处理完成，输出文件: output_video.avi" << std::endl;
    
    return 0;
}