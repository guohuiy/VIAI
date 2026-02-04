#pragma once

#include <string>
#include <vector>
#include <memory>
#include <unordered_map>
#include <functional>
#include <mutex>
#include <filesystem>

#include "plugin_interface.h"

namespace v8_ai {

// 插件句柄
struct PluginHandle {
    std::string id;
    std::string path;
    std::string name;
    std::string version;
    std::shared_ptr<IPlugin> instance;
    bool is_loaded = false;
    bool is_initialized = false;
};

// 插件发现器
class PluginDiscoverer {
private:
    std::vector<std::string> plugin_paths_;
    std::mutex mutex_;
    
public:
    // 添加插件搜索路径
    void addPluginPath(const std::string& path);
    
    // 扫描插件
    std::vector<std::string> discoverPlugins() const;
    
    // 验证插件
    bool validatePlugin(const std::string& plugin_path) const;
    
    // 获取插件信息
    PluginInfo getPluginInfo(const std::string& plugin_path) const;
};

// 插件加载器
class PluginLoader {
private:
    std::unordered_map<std::string, void*> loaded_libraries_;
    std::mutex mutex_;
    
public:
    // 加载插件库
    std::shared_ptr<IPlugin> loadPlugin(const std::string& plugin_path);
    
    // 卸载插件库
    bool unloadPlugin(const std::string& plugin_path);
    
    // 获取已加载的插件列表
    std::vector<std::string> getLoadedPlugins() const;
    
    // 检查插件是否已加载
    bool isPluginLoaded(const std::string& plugin_path) const;
    
private:
    // 平台特定的库加载
    void* loadLibrary(const std::string& path);
    void unloadLibrary(void* handle);
    void* getSymbol(void* handle, const std::string& symbol);
};

// 插件管理器
class PluginManager {
private:
    std::unordered_map<std::string, PluginHandle> plugins_;
    std::unordered_map<std::string, PluginFactory> factories_;
    std::unique_ptr<PluginDiscoverer> discoverer_;
    std::unique_ptr<PluginLoader> loader_;
    std::mutex mutex_;
    
    // 插件配置
    std::string plugin_directory_;
    bool auto_discover_;
    bool auto_load_;
    
public:
    // 构造函数
    PluginManager(const std::string& plugin_directory = "plugins/", 
                 bool auto_discover = true, bool auto_load = true);
    
    // 析构函数
    ~PluginManager();
    
    // 插件管理
    bool loadPlugin(const std::string& plugin_path);
    bool unloadPlugin(const std::string& plugin_id);
    bool unloadAll();
    
    // 插件发现
    std::vector<PluginInfo> discoverPlugins() const;
    std::vector<PluginInfo> listPlugins() const;
    
    // 插件获取
    std::shared_ptr<IPlugin> getPlugin(const std::string& plugin_id);
    std::vector<std::shared_ptr<IPlugin>> getPluginsByType(PluginType type);
    
    // 插件注册
    bool registerPlugin(const std::string& name, PluginFactory factory);
    bool unregisterPlugin(const std::string& name);
    
    // 插件信息
    PluginInfo getPluginInfo(const std::string& plugin_id) const;
    std::vector<PluginInfo> getPluginInfos() const;
    
    // 插件状态
    bool isPluginLoaded(const std::string& plugin_id) const;
    bool isPluginInitialized(const std::string& plugin_id) const;
    size_t getPluginCount() const;
    
    // 配置管理
    void setPluginDirectory(const std::string& directory);
    std::string getPluginDirectory() const;
    
    // 性能监控
    struct PluginStats {
        std::string plugin_id;
        size_t load_count = 0;
        size_t unload_count = 0;
        size_t error_count = 0;
        double total_load_time = 0.0;
        double average_load_time = 0.0;
    };
    
    std::vector<PluginStats> getPluginStats() const;
    void resetPluginStats();
    
private:
    // 内部辅助函数
    std::string generatePluginId(const std::string& path) const;
    bool validatePluginConfig(const PluginConfig& config) const;
    void updatePluginStats(const std::string& plugin_id, const std::string& operation, double time);
};

// 插件配置管理器
class PluginConfigManager {
private:
    std::string config_file_;
    std::unordered_map<std::string, PluginConfig> configs_;
    std::mutex mutex_;
    
public:
    // 构造函数
    PluginConfigManager(const std::string& config_file = "config/plugins.yaml");
    
    // 配置管理
    bool loadConfig();
    bool saveConfig() const;
    
    // 插件配置
    bool setPluginConfig(const std::string& plugin_id, const PluginConfig& config);
    PluginConfig getPluginConfig(const std::string& plugin_id) const;
    std::vector<PluginConfig> getAllConfigs() const;
    
    // 配置验证
    bool validateConfig(const PluginConfig& config) const;
    std::vector<std::string> validateAllConfigs() const;
    
    // 配置文件管理
    void setConfigFile(const std::string& file);
    std::string getConfigFile() const;
    
private:
    // YAML 序列化
    bool serializeToYAML(const std::string& file) const;
    bool deserializeFromYAML(const std::string& file);
};

// 插件生命周期管理器
class PluginLifecycleManager {
private:
    std::shared_ptr<PluginManager> plugin_manager_;
    std::shared_ptr<PluginConfigManager> config_manager_;
    std::mutex mutex_;
    
public:
    // 构造函数
    PluginLifecycleManager(std::shared_ptr<PluginManager> plugin_manager,
                          std::shared_ptr<PluginConfigManager> config_manager);
    
    // 生命周期管理
    bool initializePlugin(const std::string& plugin_id);
    bool shutdownPlugin(const std::string& plugin_id);
    bool restartPlugin(const std::string& plugin_id);
    
    // 批量操作
    bool initializeAllPlugins();
    bool shutdownAllPlugins();
    bool restartAllPlugins();
    
    // 热插拔支持
    bool hotLoadPlugin(const std::string& plugin_path);
    bool hotUnloadPlugin(const std::string& plugin_id);
    
    // 插件依赖管理
    bool checkDependencies(const std::string& plugin_id) const;
    std::vector<std::string> getPluginDependencies(const std::string& plugin_id) const;
    
    // 插件版本管理
    bool checkPluginVersion(const std::string& plugin_id, const std::string& required_version) const;
    std::string getPluginVersion(const std::string& plugin_id) const;
    
private:
    // 内部辅助函数
    bool validatePluginState(const std::string& plugin_id) const;
    bool resolvePluginDependencies(const std::string& plugin_id, std::vector<std::string>& dependencies) const;
};

// 插件工厂注册宏
#define REGISTER_PLUGIN_FACTORY(name, factory_func) \
    static bool __register_##name##__ = []() { \
        PluginManager::getInstance()->registerPlugin(name, factory_func); \
        return true; \
    }();

// 单例插件管理器
class PluginManagerSingleton {
private:
    static std::unique_ptr<PluginManager> instance_;
    static std::mutex mutex_;
    
public:
    static PluginManager& getInstance() {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!instance_) {
            instance_ = std::make_unique<PluginManager>();
        }
        return *instance_;
    }
    
    static void destroy() {
        std::lock_guard<std::mutex> lock(mutex_);
        instance_.reset();
    }
};

} // namespace v8_ai