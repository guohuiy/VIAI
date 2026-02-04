#pragma once

#include <string>
#include <vector>
#include <memory>
#include <opencv2/opencv.hpp>

namespace v8_ai {

// 插件类型枚举
enum class PluginType {
    DETECTOR,
    SEGMENTER,
    CLASSIFIER,
    CUSTOM
};

// 插件配置结构
struct PluginConfig {
    std::string name;
    std::string type;
    std::string model_path;
    std::string backend;
    std::string precision;
    int batch_size = 1;
    bool enable_async = true;
    bool enable_profiling = false;
    
    // 扩展配置
    std::map<std::string, std::string> extra_params;
};

// 插件输入结构
struct PluginInput {
    cv::Mat image;
    std::vector<cv::Mat> images;  // 批处理输入
    std::map<std::string, cv::Mat> named_inputs;
    
    // 构造函数
    PluginInput() = default;
    PluginInput(const cv::Mat& img) : image(img) {}
    PluginInput(const std::vector<cv::Mat>& imgs) : images(imgs) {}
};

// 插件输出结构
struct PluginOutput {
    std::vector<cv::Rect> boxes;
    std::vector<float> scores;
    std::vector<int> class_ids;
    cv::Mat segmentation_mask;
    std::vector<std::string> labels;
    
    // 扩展输出
    std::map<std::string, cv::Mat> named_outputs;
    std::map<std::string, float> metrics;
    
    // 清理函数
    void clear() {
        boxes.clear();
        scores.clear();
        class_ids.clear();
        segmentation_mask.release();
        labels.clear();
        named_outputs.clear();
        metrics.clear();
    }
};

// 插件结果枚举
enum class PluginResult {
    SUCCESS,
    ERROR,
    TIMEOUT,
    INVALID_INPUT,
    MODEL_NOT_LOADED
};

// 插件信息结构
struct PluginInfo {
    std::string name;
    std::string version;
    std::string author;
    std::string description;
    PluginType type;
    std::vector<std::string> supported_backends;
    std::vector<std::string> supported_formats;
    bool is_loaded = false;
    bool is_initialized = false;
};

// 性能统计结构
struct PerformanceStats {
    double avg_inference_time = 0.0;
    double max_inference_time = 0.0;
    double min_inference_time = 0.0;
    double total_inference_time = 0.0;
    size_t total_inferences = 0;
    double fps = 0.0;
    
    // 内存使用统计
    size_t gpu_memory_used = 0;
    size_t cpu_memory_used = 0;
    
    // 重置统计
    void reset() {
        avg_inference_time = 0.0;
        max_inference_time = 0.0;
        min_inference_time = 0.0;
        total_inference_time = 0.0;
        total_inferences = 0;
        fps = 0.0;
        gpu_memory_used = 0;
        cpu_memory_used = 0;
    }
    
    // 更新统计
    void update(double inference_time) {
        total_inferences++;
        total_inference_time += inference_time;
        avg_inference_time = total_inference_time / total_inferences;
        
        if (inference_time > max_inference_time) {
            max_inference_time = inference_time;
        }
        
        if (min_inference_time == 0.0 || inference_time < min_inference_time) {
            min_inference_time = inference_time;
        }
        
        fps = 1000.0 / avg_inference_time;
    }
};

// 插件接口基类
class IPlugin {
public:
    virtual ~IPlugin() = default;
    
    // 插件生命周期
    virtual bool initialize(const PluginConfig& config) = 0;
    virtual bool execute(const PluginInput& input, PluginOutput& output) = 0;
    virtual void cleanup() = 0;
    
    // 插件信息
    virtual PluginInfo getInfo() const = 0;
    virtual PluginType getType() const = 0;
    
    // 性能监控
    virtual PerformanceStats getPerformanceStats() const = 0;
    
    // 状态查询
    virtual bool isInitialized() const = 0;
    virtual bool isModelLoaded() const = 0;
    
    // 配置管理
    virtual bool updateConfig(const PluginConfig& config) = 0;
    virtual PluginConfig getConfig() const = 0;
};

// 插件工厂函数类型
using PluginFactory = std::function<std::shared_ptr<IPlugin>()>;

// 插件注册宏
#define REGISTER_PLUGIN(name, plugin_class) \
    extern "C" __declspec(dllexport) std::shared_ptr<IPlugin> create_plugin() { \
        return std::make_shared<plugin_class>(); \
    } \
    extern "C" __declspec(dllexport) const char* get_plugin_name() { \
        return name; \
    }

} // namespace v8_ai