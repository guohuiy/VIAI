#include <opencv2/opencv.hpp>
#include <opencv2/objdetect.hpp>
#include <iostream>

int main() {
    // 加载人脸检测器
    cv::CascadeClassifier face_cascade;
    if (!face_cascade.load("haarcascade_frontalface_default.xml")) {
        std::cout << "无法加载人脸检测器文件" << std::endl;
        return -1;
    }
    
    // 打开摄像头
    cv::VideoCapture cap(0);
    if (!cap.isOpened()) {
        std::cout << "无法打开摄像头" << std::endl;
        return -1;
    }
    
    cv::Mat frame, gray;
    std::vector<cv::Rect> faces;
    
    while (true) {
        // 读取帧
        cap >> frame;
        if (frame.empty()) break;
        
        // 转换为灰度图像
        cv::cvtColor(frame, gray, cv::COLOR_BGR2GRAY);
        
        // 检测人脸
        face_cascade.detectMultiScale(gray, faces, 1.1, 3, 0, cv::Size(30, 30));
        
        // 绘制检测结果
        for (const auto& face : faces) {
            cv::rectangle(frame, face, cv::Scalar(255, 0, 0), 2);
            cv::putText(frame, "Face", cv::Point(face.x, face.y - 10),
                       cv::FONT_HERSHEY_SIMPLEX, 0.9, cv::Scalar(36, 255, 12), 2);
        }
        
        // 显示结果
        cv::imshow("人脸检测", frame);
        
        // 按ESC键退出
        if (cv::waitKey(30) == 27) break;
    }
    
    cap.release();
    cv::destroyAllWindows();
    
    return 0;
}