#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // 读取图像
    cv::Mat image = cv::imread("input_image.jpg");
    
    if (image.empty()) {
        std::cout << "无法读取图像文件" << std::endl;
        return -1;
    }
    
    cv::Mat result;
    
    // 1. 高斯模糊
    cv::GaussianBlur(image, result, cv::Size(15, 15), 0);
    cv::imshow("高斯模糊", result);
    cv::imwrite("gaussian_blur.jpg", result);
    cv::waitKey(0);
    
    // 2. 中值滤波
    cv::medianBlur(image, result, 5);
    cv::imshow("中值滤波", result);
    cv::imwrite("median_filter.jpg", result);
    cv::waitKey(0);
    
    // 3. 双边滤波
    cv::bilateralFilter(image, result, 9, 75, 75);
    cv::imshow("双边滤波", result);
    cv::imwrite("bilateral_filter.jpg", result);
    cv::waitKey(0);
    
    // 4. 边缘检测
    cv::Mat gray, edges;
    cv::cvtColor(image, gray, cv::COLOR_BGR2GRAY);
    cv::Canny(gray, edges, 50, 150);
    cv::imshow("Canny边缘检测", edges);
    cv::imwrite("canny_edges.jpg", edges);
    cv::waitKey(0);
    
    // 5. 形态学操作
    cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(5, 5));
    
    // 腐蚀
    cv::erode(image, result, kernel);
    cv::imshow("腐蚀", result);
    cv::imwrite("erosion.jpg", result);
    cv::waitKey(0);
    
    // 膨胀
    cv::dilate(image, result, kernel);
    cv::imshow("膨胀", result);
    cv::imwrite("dilation.jpg", result);
    cv::waitKey(0);
    
    // 开运算（先腐蚀后膨胀）
    cv::morphologyEx(image, result, cv::MORPH_OPEN, kernel);
    cv::imshow("开运算", result);
    cv::imwrite("opening.jpg", result);
    cv::waitKey(0);
    
    // 闭运算（先膨胀后腐蚀）
    cv::morphologyEx(image, result, cv::MORPH_CLOSE, kernel);
    cv::imshow("闭运算", result);
    cv::imwrite("closing.jpg", result);
    cv::waitKey(0);
    
    // 6. 直方图均衡化
    cv::Mat equalized;
    if (image.channels() == 3) {
        cv::Mat hsv;
        cv::cvtColor(image, hsv, cv::COLOR_BGR2HSV);
        std::vector<cv::Mat> channels;
        cv::split(hsv, channels);
        cv::equalizeHist(channels[2], channels[2]);
        cv::merge(channels, hsv);
        cv::cvtColor(hsv, equalized, cv::COLOR_HSV2BGR);
    } else {
        cv::equalizeHist(gray, equalized);
    }
    cv::imshow("直方图均衡化", equalized);
    cv::imwrite("histogram_equalization.jpg", equalized);
    cv::waitKey(0);
    
    // 7. 自定义卷积核
    cv::Mat kernel_custom = (cv::Mat_<float>(3, 3) << 
                           -1, -1, -1,
                           -1,  8, -1,
                           -1, -1, -1);
    cv::filter2D(image, result, -1, kernel_custom);
    cv::imshow("自定义卷积核", result);
    cv::imwrite("custom_filter.jpg", result);
    cv::waitKey(0);
    
    cv::destroyAllWindows();
    
    std::cout << "图像滤波处理完成，所有结果已保存" << std::endl;
    
    return 0;
}