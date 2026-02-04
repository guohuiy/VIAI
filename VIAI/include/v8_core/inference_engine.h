#pragma once

#include <string>
#include <vector>
#include <memory>
#include <future>
#include <opencv2/opencv.hpp>

namespace v8_ai {

// 设备类型枚举
enum class DeviceType {
    CPU,
    GPU,
    AUTO
};

// 设备信息结构
struct DeviceInfo {
    std::string name;
    DeviceType type;
    int device_id = 0;
    size_t memory_total = 0;
    size_t memory_used = 0;
    size_t memory_free = 0;
    float utilization = 0.0f;
};

// 内存信息结构
struct MemoryInfo {
    size_t total_gpu_memory = 0;
    size_t used_gpu_memory = 0;
    size_t available_gpu_memory = 0;
    size_t total_cpu_memory = 0;
    size_t used_cpu_memory = 0;
    size_t available_cpu_memory = 0;
};

// 模型配置结构
struct ModelConfig {
    std::string model_path;
    std::string backend;
    std::string precision;
    DeviceType device = DeviceType::AUTO;
    int batch_size = 1;
    bool enable_fp16 = false;
    bool enable_int8 = false;
    bool enable_dynamic_shape = true;
    size_t workspace_size = 256 * 1024 * 1024; // 256MB
    
    // 输入输出配置
    std::vector<int> input_shape;
    std::vector<std::string> input_names;
    std::vector<std::string> output_names;
    
    // 优化配置
    bool enable_layer_fusion = true;
    bool enable_tensor_fusion = true;
    bool enable_constant_folding = true;
};

// 推理结果结构
struct InferenceResult {
    std::vector<cv::Mat> outputs;
    std::map<std::string, cv::Mat> named_outputs;
    double inference_time = 0.0;
    double preprocessing_time = 0.0;
    double postprocessing_time = 0.0;
    bool success = false;
    std::string error_message;
    
    // 清理函数
    void clear() {
        outputs.clear();
        named_outputs.clear();
        inference_time = 0.0;
        preprocessing_time = 0.0;
        postprocessing_time = 0.0;
        success = false;
        error_message.clear();
    }
};

// 推理引擎接口
class IInferenceEngine {
public:
    virtual ~IInferenceEngine() = default;
    
    // 模型管理
    virtual bool loadModel(const ModelConfig& config) = 0;
    virtual bool unloadModel() = 0;
    virtual bool isModelLoaded() const = 0;
    
    // 推理接口
    virtual InferenceResult infer(const cv::Mat& input) = 0;
    virtual std::future<InferenceResult> inferAsync(const cv::Mat& input) = 0;
    virtual std::vector<InferenceResult> inferBatch(const std::vector<cv::Mat>& inputs) = 0;
    
    // 设备信息
    virtual DeviceInfo getDeviceInfo() const = 0;
    virtual MemoryInfo getMemoryInfo() const = 0;
    
    // 性能监控
    virtual double getAverageInferenceTime() const = 0;
    virtual double getFPS() const = 0;
    virtual size_t getTotalInferences() const = 0;
    
    // 配置管理
    virtual bool updateConfig(const ModelConfig& config) = 0;
    virtual ModelConfig getConfig() const = 0;
    
    // 后端信息
    virtual std::string getBackendName() const = 0;
    virtual std::string getBackendVersion() const = 0;
    virtual std::vector<std::string> getSupportedPrecisions() const = 0;
};

// 推理引擎工厂
class InferenceEngineFactory {
public:
    static std::unique_ptr<IInferenceEngine> createEngine(const std::string& backend);
    static std::vector<std::string> getAvailableBackends();
    static bool isBackendAvailable(const std::string& backend);
};

// 推理引擎管理器
class InferenceEngineManager {
private:
    std::vector<std::unique_ptr<IInferenceEngine>> engines_;
    std::mutex mutex_;
    
public:
    // 创建引擎
    std::unique_ptr<IInferenceEngine> createEngine(const std::string& backend);
    
    // 获取可用设备
    std::vector<DeviceInfo> getAvailableDevices() const;
    
    // 获取最佳设备
    DeviceInfo getBestDevice() const;
    
    // 内存管理
    MemoryInfo getGlobalMemoryInfo() const;
    bool canAllocate(size_t size, DeviceType device) const;
};

// 推理优化器
class InferenceOptimizer {
public:
    struct OptimizationConfig {
        bool enable_mixed_precision = true;
        bool enable_layer_fusion = true;
        bool enable_tensor_fusion = true;
        bool enable_constant_folding = true;
        bool enable_kernel_fusion = true;
        bool enable_memory_optimization = true;
        size_t max_workspace_size = 1024 * 1024 * 1024; // 1GB
    };
    
    static OptimizationConfig optimizeFor4GBVRAM();
    static OptimizationConfig optimizeFor8GBVRAM();
    static OptimizationConfig optimizeForCPU();
    
    static void applyOptimizations(ModelConfig& config, const OptimizationConfig& opt_config);
};

// 推理流水线
class InferencePipeline {
private:
    std::unique_ptr<IInferenceEngine> engine_;
    std::vector<std::function<cv::Mat(const cv::Mat&)>> preprocessors_;
    std::vector<std::function<void(InferenceResult&)>> postprocessors_;
    
public:
    InferencePipeline(std::unique_ptr<IInferenceEngine> engine);
    
    // 添加预处理步骤
    void addPreprocessor(std::function<cv::Mat(const cv::Mat&)> preprocessor);
    
    // 添加后处理步骤
    void addPostprocessor(std::function<void(InferenceResult&)> postprocessor);
    
    // 执行推理流水线
    InferenceResult run(const cv::Mat& input);
    std::future<InferenceResult> runAsync(const cv::Mat& input);
    std::vector<InferenceResult> runBatch(const std::vector<cv::Mat>& inputs);
    
    // 性能统计
    double getAverageLatency() const;
    double getThroughput() const;
    size_t getTotalProcessed() const;
};

} // namespace v8_ai