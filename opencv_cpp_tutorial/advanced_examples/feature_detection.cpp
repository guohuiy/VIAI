#include <opencv2/opencv.hpp>
#include <opencv2/features2d.hpp>
#include <iostream>

int main() {
    // 读取图像
    cv::Mat image = cv::imread("input_image.jpg");
    
    if (image.empty()) {
        std::cout << "无法读取图像文件" << std::endl;
        return -1;
    }
    
    // 创建ORB特征检测器
    cv::Ptr<cv::ORB> orb = cv::ORB::create(500);  // 检测500个特征点
    
    // 检测关键点和计算描述符
    std::vector<cv::KeyPoint> keypoints;
    cv::Mat descriptors;
    orb->detectAndCompute(image, cv::noArray(), keypoints, descriptors);
    
    std::cout << "检测到 " << keypoints.size() << " 个特征点" << std::endl;
    
    // 绘制关键点
    cv::Mat output;
    cv::drawKeypoints(image, keypoints, output, cv::Scalar::all(-1), 
                     cv::DrawMatchesFlags::DRAW_RICH_KEYPOINTS);
    
    // 显示结果
    cv::imshow("特征检测结果", output);
    cv::waitKey(0);
    
    // 保存结果
    cv::imwrite("feature_detection_result.jpg", output);
    
    // 演示特征匹配
    cv::Mat image2 = cv::imread("input_image2.jpg");
    if (!image2.empty()) {
        std::vector<cv::KeyPoint> keypoints2;
        cv::Mat descriptors2;
        orb->detectAndCompute(image2, cv::noArray(), keypoints2, descriptors2);
        
        // 创建BFMatcher进行特征匹配
        cv::BFMatcher matcher(cv::NORM_HAMMING);
        std::vector<cv::DMatch> matches;
        matcher.match(descriptors, descriptors2, matches);
        
        // 绘制匹配结果
        cv::Mat match_output;
        cv::drawMatches(image, keypoints, image2, keypoints2, matches, match_output);
        
        cv::imshow("特征匹配", match_output);
        cv::waitKey(0);
        cv::imwrite("feature_matching_result.jpg", match_output);
    }
    
    return 0;
}