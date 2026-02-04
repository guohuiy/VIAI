#include "v8_core/plugin_manager.h"
#include <iostream>
#include <fstream>
#include <dlfcn.h>

namespace v8_ai {

// 插件发现器实现
void PluginDiscoverer::addPluginPath(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    plugin_paths_.push_back(path);
}

std::vector<std::string> PluginDiscoverer::discoverPlugins() const {
    std::vector<std::string> plugins;
    
    for (const auto& path : plugin_paths_) {
        try {
            for (const auto& entry : std::filesystem::directory_iterator(path)) {
                if (entry.is_regular_file()) {
                    std::string filename = entry.path().filename().string();
                    if (filename.find("plugin") != std::string::npos && 
                        (filename.ends_with(".dll") || filename.ends_with(".so"))) {
                        plugins.push_back(entry.path().string());
                    }
                }
            }
        } catch (const std::filesystem::filesystem_error& e) {
            std::cerr << "Error scanning directory " << path << ": " << e.what() << std::endl;
        }
    }
    
    return plugins;
}

bool PluginDiscoverer::validatePlugin(const std::string& plugin_path) const {
    // 检查文件是否存在
    if (!std::filesystem::exists(plugin_path)) {
        return false;
    }
    
    // 检查文件权限
    try {
        auto status = std::filesystem::status(plugin_path);
        if (!std::filesystem::is_regular_file(status) || 
            !(status.permissions() & std::filesystem::perms::owner_read)) {
            return false;
        }
    } catch (const std::filesystem::filesystem_error&) {
        return false;
    }
    
    return true;
}

PluginInfo PluginDiscoverer::getPluginInfo(const std::string& plugin_path) const {
    PluginInfo info;
    info.name = "Unknown";
    info.version = "1.0.0";
    info.author = "Unknown";
    info.description = "Plugin information not available";
    info.type = PluginType::CUSTOM;
    info.is_loaded = false;
    info.is_initialized = false;
    
    // 尝试加载插件获取信息
    void* handle = dlopen(plugin_path.c_str(), RTLD_LAZY);
    if (handle) {
        auto get_name_func = (const char* (*)())dlsym(handle, "get_plugin_name");
        if (get_name_func) {
            info.name = get_name_func();
        }
        dlclose(handle);
    }
    
    return info;
}

// 插件加载器实现
std::shared_ptr<IPlugin> PluginLoader::loadPlugin(const std::string& plugin_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 检查是否已加载
    if (isPluginLoaded(plugin_path)) {
        return nullptr;
    }
    
    // 加载库
    void* handle = loadLibrary(plugin_path);
    if (!handle) {
        return nullptr;
    }
    
    // 获取创建函数
    auto create_func = (std::shared_ptr<IPlugin> (*)())getSymbol(handle, "create_plugin");
    if (!create_func) {
        unloadLibrary(handle);
        return nullptr;
    }
    
    // 创建插件实例
    auto plugin = create_func();
    if (plugin) {
        loaded_libraries_[plugin_path] = handle;
    }
    
    return plugin;
}

bool PluginLoader::unloadPlugin(const std::string& plugin_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = loaded_libraries_.find(plugin_path);
    if (it != loaded_libraries_.end()) {
        unloadLibrary(it->second);
        loaded_libraries_.erase(it);
        return true;
    }
    
    return false;
}

std::vector<std::string> PluginLoader::getLoadedPlugins() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> plugins;
    
    for (const auto& pair : loaded_libraries_) {
        plugins.push_back(pair.first);
    }
    
    return plugins;
}

bool PluginLoader::isPluginLoaded(const std::string& plugin_path) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return loaded_libraries_.find(plugin_path) != loaded_libraries_.end();
}

void* PluginLoader::loadLibrary(const std::string& path) {
#ifdef _WIN32
    return LoadLibraryA(path.c_str());
#else
    return dlopen(path.c_str(), RTLD_LAZY);
#endif
}

void PluginLoader::unloadLibrary(void* handle) {
#ifdef _WIN32
    FreeLibrary((HMODULE)handle);
#else
    dlclose(handle);
#endif
}

void* PluginLoader::getSymbol(void* handle, const std::string& symbol) {
#ifdef _WIN32
    return GetProcAddress((HMODULE)handle, symbol.c_str());
#else
    return dlsym(handle, symbol.c_str());
#endif
}

// 插件管理器实现
PluginManager::PluginManager(const std::string& plugin_directory, 
                           bool auto_discover, bool auto_load)
    : plugin_directory_(plugin_directory), auto_discover_(auto_discover), auto_load_(auto_load) {
    discoverer_ = std::make_unique<PluginDiscoverer>();
    loader_ = std::make_unique<PluginLoader>();
    
    // 添加默认插件路径
    discoverer_->addPluginPath(plugin_directory_);
    
    if (auto_discover_) {
        auto plugins = discoverPlugins();
        if (auto_load_) {
            for (const auto& plugin : plugins) {
                loadPlugin(plugin);
            }
        }
    }
}

PluginManager::~PluginManager() {
    unloadAll();
}

bool PluginManager::loadPlugin(const std::string& plugin_path) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    std::string plugin_id = generatePluginId(plugin_path);
    
    // 检查是否已加载
    if (plugins_.find(plugin_id) != plugins_.end()) {
        return true;  // 已经加载
    }
    
    // 加载插件
    auto plugin = loader_->loadPlugin(plugin_path);
    if (!plugin) {
        return false;
    }
    
    // 创建插件句柄
    PluginHandle handle;
    handle.id = plugin_id;
    handle.path = plugin_path;
    handle.instance = plugin;
    handle.is_loaded = true;
    handle.is_initialized = false;
    
    // 获取插件信息
    auto info = plugin->getInfo();
    handle.name = info.name;
    handle.version = info.version;
    
    plugins_[plugin_id] = handle;
    
    return true;
}

bool PluginManager::unloadPlugin(const std::string& plugin_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = plugins_.find(plugin_id);
    if (it == plugins_.end()) {
        return false;
    }
    
    // 清理插件
    if (it->second.is_initialized) {
        it->second.instance->cleanup();
    }
    
    // 卸载库
    loader_->unloadPlugin(it->second.path);
    
    // 移除插件
    plugins_.erase(it);
    
    return true;
}

bool PluginManager::unloadAll() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    for (auto& pair : plugins_) {
        if (pair.second.is_initialized) {
            pair.second.instance->cleanup();
        }
        loader_->unloadPlugin(pair.second.path);
    }
    
    plugins_.clear();
    return true;
}

std::vector<PluginInfo> PluginManager::discoverPlugins() const {
    auto plugin_paths = discoverer_->discoverPlugins();
    std::vector<PluginInfo> plugins;
    
    for (const auto& path : plugin_paths) {
        if (discoverer_->validatePlugin(path)) {
            auto info = discoverer_->getPluginInfo(path);
            plugins.push_back(info);
        }
    }
    
    return plugins;
}

std::vector<PluginInfo> PluginManager::listPlugins() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<PluginInfo> plugins;
    
    for (const auto& pair : plugins_) {
        plugins.push_back(pair.second.instance->getInfo());
    }
    
    return plugins;
}

std::shared_ptr<IPlugin> PluginManager::getPlugin(const std::string& plugin_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = plugins_.find(plugin_id);
    if (it != plugins_.end()) {
        return it->second.instance;
    }
    
    return nullptr;
}

std::vector<std::shared_ptr<IPlugin>> PluginManager::getPluginsByType(PluginType type) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::shared_ptr<IPlugin>> plugins;
    
    for (const auto& pair : plugins_) {
        if (pair.second.instance->getType() == type) {
            plugins.push_back(pair.second.instance);
        }
    }
    
    return plugins;
}

bool PluginManager::registerPlugin(const std::string& name, PluginFactory factory) {
    std::lock_guard<std::mutex> lock(mutex_);
    factories_[name] = factory;
    return true;
}

bool PluginManager::unregisterPlugin(const std::string& name) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = factories_.find(name);
    if (it != factories_.end()) {
        factories_.erase(it);
        return true;
    }
    return false;
}

PluginInfo PluginManager::getPluginInfo(const std::string& plugin_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = plugins_.find(plugin_id);
    if (it != plugins_.end()) {
        return it->second.instance->getInfo();
    }
    
    return PluginInfo{};
}

std::vector<PluginInfo> PluginManager::getPluginInfos() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<PluginInfo> infos;
    
    for (const auto& pair : plugins_) {
        infos.push_back(pair.second.instance->getInfo());
    }
    
    return infos;
}

bool PluginManager::isPluginLoaded(const std::string& plugin_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return plugins_.find(plugin_id) != plugins_.end();
}

bool PluginManager::isPluginInitialized(const std::string& plugin_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = plugins_.find(plugin_id);
    if (it != plugins_.end()) {
        return it->second.is_initialized;
    }
    
    return false;
}

size_t PluginManager::getPluginCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return plugins_.size();
}

void PluginManager::setPluginDirectory(const std::string& directory) {
    std::lock_guard<std::mutex> lock(mutex_);
    plugin_directory_ = directory;
    discoverer_->addPluginPath(directory);
}

std::string PluginManager::getPluginDirectory() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return plugin_directory_;
}

std::vector<PluginManager::PluginStats> PluginManager::getPluginStats() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<PluginStats> stats;
    
    // 这里应该有实际的统计信息收集逻辑
    // 目前返回空的统计信息
    return stats;
}

void PluginManager::resetPluginStats() {
    std::lock_guard<std::mutex> lock(mutex_);
    // 重置统计信息
}

std::string PluginManager::generatePluginId(const std::string& path) const {
    // 简单的ID生成，实际应该使用更复杂的逻辑
    return std::filesystem::path(path).filename().string();
}

bool PluginManager::validatePluginConfig(const PluginConfig& config) const {
    if (config.name.empty() || config.model_path.empty()) {
        return false;
    }
    
    if (config.batch_size <= 0) {
        return false;
    }
    
    return true;
}

void PluginManager::updatePluginStats(const std::string& plugin_id, 
                                    const std::string& operation, 
                                    double time) {
    // 更新插件统计信息
    // 这里应该有实际的统计逻辑
}

// 插件配置管理器实现
PluginConfigManager::PluginConfigManager(const std::string& config_file)
    : config_file_(config_file) {
    loadConfig();
}

bool PluginConfigManager::loadConfig() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!std::filesystem::exists(config_file_)) {
        return true;  // 配置文件不存在是正常的
    }
    
    return deserializeFromYAML(config_file_);
}

bool PluginConfigManager::saveConfig() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return serializeToYAML(config_file_);
}

bool PluginConfigManager::setPluginConfig(const std::string& plugin_id, 
                                        const PluginConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!validateConfig(config)) {
        return false;
    }
    
    configs_[plugin_id] = config;
    return saveConfig();
}

PluginConfig PluginConfigManager::getPluginConfig(const std::string& plugin_id) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = configs_.find(plugin_id);
    if (it != configs_.end()) {
        return it->second;
    }
    
    return PluginConfig{};
}

std::vector<PluginConfig> PluginConfigManager::getAllConfigs() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<PluginConfig> configs;
    
    for (const auto& pair : configs_) {
        configs.push_back(pair.second);
    }
    
    return configs;
}

bool PluginConfigManager::validateConfig(const PluginConfig& config) const {
    if (config.name.empty() || config.model_path.empty()) {
        return false;
    }
    
    if (config.batch_size <= 0) {
        return false;
    }
    
    return true;
}

std::vector<std::string> PluginConfigManager::validateAllConfigs() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> errors;
    
    for (const auto& pair : configs_) {
        if (!validateConfig(pair.second)) {
            errors.push_back("Invalid config for plugin: " + pair.first);
        }
    }
    
    return errors;
}

void PluginConfigManager::setConfigFile(const std::string& file) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_file_ = file;
}

std::string PluginConfigManager::getConfigFile() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return config_file_;
}

bool PluginConfigManager::serializeToYAML(const std::string& file) const {
    // YAML 序列化实现
    // 这里应该使用 YAML 库来序列化配置
    return true;
}

bool PluginConfigManager::deserializeFromYAML(const std::string& file) {
    // YAML 反序列化实现
    // 这里应该使用 YAML 库来反序列化配置
    return true;
}

// 插件生命周期管理器实现
PluginLifecycleManager::PluginLifecycleManager(
    std::shared_ptr<PluginManager> plugin_manager,
    std::shared_ptr<PluginConfigManager> config_manager)
    : plugin_manager_(plugin_manager), config_manager_(config_manager) {
}

bool PluginLifecycleManager::initializePlugin(const std::string& plugin_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto plugin = plugin_manager_->getPlugin(plugin_id);
    if (!plugin) {
        return false;
    }
    
    auto config = config_manager_->getPluginConfig(plugin_id);
    if (!config_manager_->validateConfig(config)) {
        return false;
    }
    
    if (!plugin->initialize(config)) {
        return false;
    }
    
    // 更新插件状态
    // 这里应该有实际的状态更新逻辑
    
    return true;
}

bool PluginLifecycleManager::shutdownPlugin(const std::string& plugin_id) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto plugin = plugin_manager_->getPlugin(plugin_id);
    if (!plugin) {
        return false;
    }
    
    plugin->cleanup();
    
    return true;
}

bool PluginLifecycleManager::restartPlugin(const std::string& plugin_id) {
    if (!shutdownPlugin(plugin_id)) {
        return false;
    }
    
    return initializePlugin(plugin_id);
}

bool PluginLifecycleManager::initializeAllPlugins() {
    auto plugins = plugin_manager_->getPluginInfos();
    
    for (const auto& info : plugins) {
        if (!initializePlugin(info.name)) {
            return false;
        }
    }
    
    return true;
}

bool PluginLifecycleManager::shutdownAllPlugins() {
    auto plugins = plugin_manager_->getPluginInfos();
    
    for (const auto& info : plugins) {
        shutdownPlugin(info.name);
    }
    
    return true;
}

bool PluginLifecycleManager::restartAllPlugins() {
    if (!shutdownAllPlugins()) {
        return false;
    }
    
    return initializeAllPlugins();
}

bool PluginLifecycleManager::hotLoadPlugin(const std::string& plugin_path) {
    if (!plugin_manager_->loadPlugin(plugin_path)) {
        return false;
    }
    
    std::string plugin_id = plugin_manager_->getPluginDirectory() + 
                           std::filesystem::path(plugin_path).filename().string();
    
    return initializePlugin(plugin_id);
}

bool PluginLifecycleManager::hotUnloadPlugin(const std::string& plugin_id) {
    if (!shutdownPlugin(plugin_id)) {
        return false;
    }
    
    return plugin_manager_->unloadPlugin(plugin_id);
}

bool PluginLifecycleManager::checkDependencies(const std::string& plugin_id) const {
    // 检查插件依赖
    // 这里应该有实际的依赖检查逻辑
    return true;
}

std::vector<std::string> PluginLifecycleManager::getPluginDependencies(
    const std::string& plugin_id) const {
    // 获取插件依赖列表
    // 这里应该有实际的依赖获取逻辑
    return {};
}

bool PluginLifecycleManager::checkPluginVersion(const std::string& plugin_id, 
                                              const std::string& required_version) const {
    auto plugin = plugin_manager_->getPlugin(plugin_id);
    if (!plugin) {
        return false;
    }
    
    auto info = plugin->getInfo();
    // 版本比较逻辑
    return info.version >= required_version;
}

std::string PluginLifecycleManager::getPluginVersion(const std::string& plugin_id) const {
    auto plugin = plugin_manager_->getPlugin(plugin_id);
    if (!plugin) {
        return "";
    }
    
    return plugin->getInfo().version;
}

bool PluginLifecycleManager::validatePluginState(const std::string& plugin_id) const {
    return plugin_manager_->isPluginLoaded(plugin_id) && 
           plugin_manager_->isPluginInitialized(plugin_id);
}

bool PluginLifecycleManager::resolvePluginDependencies(const std::string& plugin_id, 
                                                     std::vector<std::string>& dependencies) const {
    // 解析插件依赖
    // 这里应该有实际的依赖解析逻辑
    return true;
}

// 单例插件管理器
std::unique_ptr<PluginManager> PluginManagerSingleton::instance_ = nullptr;
std::mutex PluginManagerSingleton::mutex_;

} // namespace v8_ai