#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // 创建一个空白图像
    cv::Mat image = cv::Mat::zeros(400, 600, CV_8UC3);
    
    // 在图像上绘制一些形状
    cv::circle(image, cv::Point(300, 200), 100, cv::Scalar(0, 255, 0), -1);
    cv::rectangle(image, cv::Rect(100, 100, 200, 150), cv::Scalar(255, 0, 0), 2);
    cv::line(image, cv::Point(0, 0), cv::Point(600, 400), cv::Scalar(0, 0, 255), 2);
    
    // 显示图像
    cv::imshow("OpenCV Example", image);
    cv::waitKey(0);
    
    // 保存图像
    cv::imwrite("output.png", image);
    
    std::cout << "OpenCV C++ 示例程序运行成功！" << std::endl;
    std::cout << "图像已保存为 output.png" << std::endl;
    
    return 0;
}