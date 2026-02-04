#include <iostream>
#include <memory>
#include <vector>
#include <string>
#include <opencv2/opencv.hpp>

#include "v8_core/plugin_manager.h"
#include "v8_core/inference_engine.h"
#include "v8_core/memory_pool.h"

namespace v8_ai {

class V8AIApplication {
private:
    std::unique_ptr<PluginManager> plugin_manager_;
    std::unique_ptr<InferenceEngineManager> engine_manager_;
    std::unique_ptr<UnifiedMemoryManager> memory_manager_;
    
public:
    V8AIApplication() {
        initialize();
    }
    
    ~V8AIApplication() {
        cleanup();
    }
    
    bool initialize() {
        std::cout << "Initializing V8-AI Application..." << std::endl;
        
        try {
            // 初始化内存管理器
            MemoryPoolConfig cpu_config;
            cpu_config.initial_pool_size = 2 * 1024 * 1024 * 1024;  // 2GB
            cpu_config.max_pool_size = 8 * 1024 * 1024 * 1024;      // 8GB
            
            MemoryPoolConfig gpu_config;
            gpu_config.initial_pool_size = 1024 * 1024 * 1024;      // 1GB
            gpu_config.max_pool_size = 4 * 1024 * 1024 * 1024;      // 4GB
            
            memory_manager_ = std::make_unique<UnifiedMemoryManager>(cpu_config, gpu_config);
            
            // 初始化推理引擎管理器
            engine_manager_ = std::make_unique<InferenceEngineManager>();
            
            // 初始化插件管理器
            plugin_manager_ = std::make_unique<PluginManager>("plugins/", true, true);
            
            std::cout << "V8-AI Application initialized successfully!" << std::endl;
            return true;
            
        } catch (const std::exception& e) {
            std::cerr << "Failed to initialize V8-AI Application: " << e.what() << std::endl;
            return false;
        }
    }
    
    void cleanup() {
        std::cout << "Cleaning up V8-AI Application..." << std::endl;
        
        if (plugin_manager_) {
            plugin_manager_->unloadAll();
        }
        
        std::cout << "V8-AI Application cleaned up successfully!" << std::endl;
    }
    
    void run() {
        std::cout << "V8-AI Application is running..." << std::endl;
        
        // 显示系统信息
        showSystemInfo();
        
        // 显示插件信息
        showPluginInfo();
        
        // 显示内存信息
        showMemoryInfo();
        
        // 主循环
        while (true) {
            std::string command;
            std::cout << "\nV8-AI> ";
            std::getline(std::cin, command);
            
            if (command == "quit" || command == "exit") {
                break;
            } else if (command == "plugins") {
                showPluginInfo();
            } else if (command == "memory") {
                showMemoryInfo();
            } else if (command == "engines") {
                showEngineInfo();
            } else if (command == "help") {
                showHelp();
            } else if (command.empty()) {
                continue;
            } else {
                std::cout << "Unknown command. Type 'help' for available commands." << std::endl;
            }
        }
    }
    
private:
    void showSystemInfo() {
        std::cout << "\n=== System Information ===" << std::endl;
        
        // 显示设备信息
        auto devices = engine_manager_->getAvailableDevices();
        std::cout << "Available Devices:" << std::endl;
        for (const auto& device : devices) {
            std::cout << "  - " << device.name << " (" << 
                         (device.type == DeviceType::GPU ? "GPU" : "CPU") << ")" << std::endl;
            std::cout << "    Memory: " << device.memory_total / (1024 * 1024 * 1024) << "GB" << std::endl;
            std::cout << "    Used: " << device.memory_used / (1024 * 1024 * 1024) << "GB" << std::endl;
            std::cout << "    Free: " << device.memory_free / (1024 * 1024 * 1024) << "GB" << std::endl;
            std::cout << "    Utilization: " << device.utilization << "%" << std::endl;
        }
        
        // 显示支持的后端
        auto backends = InferenceEngineFactory::getAvailableBackends();
        std::cout << "\nAvailable Backends:" << std::endl;
        for (const auto& backend : backends) {
            std::cout << "  - " << backend << std::endl;
        }
    }
    
    void showPluginInfo() {
        std::cout << "\n=== Plugin Information ===" << std::endl;
        
        auto plugins = plugin_manager_->listPlugins();
        std::cout << "Loaded Plugins: " << plugins.size() << std::endl;
        
        for (const auto& plugin : plugins) {
            std::cout << "  - " << plugin.name << " (" << plugin.version << ")" << std::endl;
            std::cout << "    Type: " << getPluginTypeName(plugin.type) << std::endl;
            std::cout << "    Author: " << plugin.author << std::endl;
            std::cout << "    Description: " << plugin.description << std::endl;
        }
        
        // 显示插件统计
        auto stats = plugin_manager_->getPluginStats();
        if (!stats.empty()) {
            std::cout << "\nPlugin Statistics:" << std::endl;
            for (const auto& stat : stats) {
                std::cout << "  - " << stat.plugin_id << ":" << std::endl;
                std::cout << "    Load Count: " << stat.load_count << std::endl;
                std::cout << "    Unload Count: " << stat.unload_count << std::endl;
                std::cout << "    Error Count: " << stat.error_count << std::endl;
                std::cout << "    Average Load Time: " << stat.average_load_time << "ms" << std::endl;
            }
        }
    }
    
    void showMemoryInfo() {
        std::cout << "\n=== Memory Information ===" << std::endl;
        
        // CPU 内存信息
        auto cpu_stats = memory_manager_->getCPUStatistics();
        std::cout << "CPU Memory:" << std::endl;
        std::cout << "  Total Allocated: " << cpu_stats.total_allocated / (1024 * 1024) << "MB" << std::endl;
        std::cout << "  Peak Usage: " << cpu_stats.peak_usage / (1024 * 1024) << "MB" << std::endl;
        std::cout << "  Allocation Count: " << cpu_stats.allocation_count << std::endl;
        std::cout << "  Deallocation Count: " << cpu_stats.deallocation_count << std::endl;
        
        // GPU 内存信息
        auto gpu_stats = memory_manager_->getGPUStatistics();
        std::cout << "\nGPU Memory:" << std::endl;
        std::cout << "  Total Allocated: " << gpu_stats.total_allocated / (1024 * 1024) << "MB" << std::endl;
        std::cout << "  Peak Usage: " << gpu_stats.peak_usage / (1024 * 1024) << "MB" << std::endl;
        std::cout << "  Allocation Count: " << gpu_stats.allocation_count << std::endl;
        std::cout << "  Deallocation Count: " << gpu_stats.deallocation_count << std::endl;
        
        // 全局内存信息
        auto global_info = memory_manager_->getGlobalMemoryInfo();
        std::cout << "\nGlobal Memory:" << std::endl;
        std::cout << "  Total GPU Memory: " << global_info.total_gpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
        std::cout << "  Used GPU Memory: " << global_info.used_gpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
        std::cout << "  Available GPU Memory: " << global_info.available_gpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
        std::cout << "  Total CPU Memory: " << global_info.total_cpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
        std::cout << "  Used CPU Memory: " << global_info.used_cpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
        std::cout << "  Available CPU Memory: " << global_info.available_cpu_memory / (1024 * 1024 * 1024) << "GB" << std::endl;
    }
    
    void showEngineInfo() {
        std::cout << "\n=== Engine Information ===" << std::endl;
        
        auto devices = engine_manager_->getAvailableDevices();
        std::cout << "Available Devices:" << std::endl;
        for (const auto& device : devices) {
            std::cout << "  - " << device.name << std::endl;
            std::cout << "    Type: " << (device.type == DeviceType::GPU ? "GPU" : "CPU") << std::endl;
            std::cout << "    Memory: " << device.memory_total / (1024 * 1024 * 1024) << "GB" << std::endl;
        }
        
        auto best_device = engine_manager_->getBestDevice();
        std::cout << "\nBest Device: " << best_device.name << std::endl;
    }
    
    void showHelp() {
        std::cout << "\n=== Available Commands ===" << std::endl;
        std::cout << "  plugins    - Show plugin information" << std::endl;
        std::cout << "  memory     - Show memory information" << std::endl;
        std::cout << "  engines    - Show engine information" << std::endl;
        std::cout << "  help       - Show this help message" << std::endl;
        std::cout << "  quit/exit  - Exit the application" << std::endl;
    }
    
    std::string getPluginTypeName(PluginType type) {
        switch (type) {
            case PluginType::DETECTOR: return "Detector";
            case PluginType::SEGMENTER: return "Segmenter";
            case PluginType::CLASSIFIER: return "Classifier";
            case PluginType::CUSTOM: return "Custom";
            default: return "Unknown";
        }
    }
};

} // namespace v8_ai

int main(int argc, char* argv[]) {
    std::cout << "V8-AI - High-Performance Computer Vision Platform" << std::endl;
    std::cout << "=================================================" << std::endl;
    
    v8_ai::V8AIApplication app;
    
    if (app.initialize()) {
        app.run();
    }
    
    std::cout << "V8-AI Application terminated." << std::endl;
    return 0;
}