#include <gtest/gtest.h>
#include <memory>
#include <vector>
#include <string>

#include "v8_core/plugin_manager.h"

namespace v8_ai {

// 测试插件管理器
class PluginManagerTest : public ::testing::Test {
protected:
    void SetUp() override {
        // 设置测试环境
        plugin_manager_ = std::make_unique<PluginManager>("test_plugins/");
    }
    
    void TearDown() override {
        // 清理测试环境
        plugin_manager_->unloadAll();
    }
    
    std::unique_ptr<PluginManager> plugin_manager_;
};

// 测试插件配置
TEST_F(PluginManagerTest, PluginConfigValidation) {
    PluginConfig config;
    config.name = "test_plugin";
    config.model_path = "test_model.onnx";
    config.batch_size = 1;
    
    // 测试有效配置
    EXPECT_TRUE(plugin_manager_->validatePluginConfig(config));
    
    // 测试无效配置
    config.name = "";
    EXPECT_FALSE(plugin_manager_->validatePluginConfig(config));
    
    config.name = "test_plugin";
    config.model_path = "";
    EXPECT_FALSE(plugin_manager_->validatePluginConfig(config));
    
    config.model_path = "test_model.onnx";
    config.batch_size = 0;
    EXPECT_FALSE(plugin_manager_->validatePluginConfig(config));
}

// 测试插件信息
TEST_F(PluginManagerTest, PluginInfo) {
    PluginInfo info;
    info.name = "Test Plugin";
    info.version = "1.0.0";
    info.author = "Test Author";
    info.description = "Test Description";
    info.type = PluginType::DETECTOR;
    
    EXPECT_EQ(info.name, "Test Plugin");
    EXPECT_EQ(info.version, "1.0.0");
    EXPECT_EQ(info.type, PluginType::DETECTOR);
}

// 测试插件统计
TEST_F(PluginManagerTest, PluginStats) {
    PluginManager::PluginStats stats;
    stats.plugin_id = "test_plugin";
    stats.load_count = 5;
    stats.unload_count = 3;
    stats.error_count = 1;
    stats.total_load_time = 100.0;
    stats.average_load_time = 20.0;
    
    EXPECT_EQ(stats.plugin_id, "test_plugin");
    EXPECT_EQ(stats.load_count, 5);
    EXPECT_EQ(stats.unload_count, 3);
    EXPECT_EQ(stats.error_count, 1);
    EXPECT_DOUBLE_EQ(stats.total_load_time, 100.0);
    EXPECT_DOUBLE_EQ(stats.average_load_time, 20.0);
}

// 测试插件生命周期
class MockPlugin : public IPlugin {
public:
    bool initialize(const PluginConfig& config) override {
        initialized_ = true;
        config_ = config;
        return true;
    }
    
    PluginResult execute(const PluginInput& input, PluginOutput& output) override {
        return PluginResult::SUCCESS;
    }
    
    void cleanup() override {
        initialized_ = false;
    }
    
    PluginInfo getInfo() const override {
        PluginInfo info;
        info.name = "Mock Plugin";
        info.version = "1.0.0";
        info.type = PluginType::DETECTOR;
        return info;
    }
    
    PluginType getType() const override {
        return PluginType::DETECTOR;
    }
    
    PerformanceStats getPerformanceStats() const override {
        return PerformanceStats{};
    }
    
    bool isInitialized() const override {
        return initialized_;
    }
    
    bool isModelLoaded() const override {
        return true;
    }
    
    bool updateConfig(const PluginConfig& config) override {
        config_ = config;
        return true;
    }
    
    PluginConfig getConfig() const override {
        return config_;
    }
    
private:
    bool initialized_ = false;
    PluginConfig config_;
};

TEST_F(PluginManagerTest, PluginLifecycle) {
    // 注册插件工厂
    auto factory = []() -> std::shared_ptr<IPlugin> {
        return std::make_shared<MockPlugin>();
    };
    
    EXPECT_TRUE(plugin_manager_->registerPlugin("mock_plugin", factory));
    
    // 测试插件加载
    EXPECT_TRUE(plugin_manager_->loadPlugin("mock_plugin"));
    
    // 测试插件信息获取
    auto plugin = plugin_manager_->getPlugin("mock_plugin");
    ASSERT_NE(plugin, nullptr);
    
    PluginInfo info = plugin->getInfo();
    EXPECT_EQ(info.name, "Mock Plugin");
    EXPECT_EQ(info.type, PluginType::DETECTOR);
    
    // 测试插件状态
    EXPECT_TRUE(plugin_manager_->isPluginLoaded("mock_plugin"));
    EXPECT_TRUE(plugin_manager_->isPluginInitialized("mock_plugin"));
    
    // 测试插件数量
    EXPECT_EQ(plugin_manager_->getPluginCount(), 1);
    
    // 测试插件列表
    auto plugins = plugin_manager_->listPlugins();
    EXPECT_EQ(plugins.size(), 1);
    EXPECT_EQ(plugins[0].name, "Mock Plugin");
    
    // 测试插件卸载
    EXPECT_TRUE(plugin_manager_->unloadPlugin("mock_plugin"));
    EXPECT_FALSE(plugin_manager_->isPluginLoaded("mock_plugin"));
    EXPECT_FALSE(plugin_manager_->isPluginInitialized("mock_plugin"));
}

// 测试插件配置管理器
TEST_F(PluginManagerTest, PluginConfigManager) {
    PluginConfigManager config_manager("test_config.yaml");
    
    // 测试配置设置
    PluginConfig config;
    config.name = "test_plugin";
    config.model_path = "test_model.onnx";
    config.batch_size = 1;
    
    EXPECT_TRUE(config_manager.setPluginConfig("test_plugin", config));
    
    // 测试配置获取
    PluginConfig retrieved_config = config_manager.getPluginConfig("test_plugin");
    EXPECT_EQ(retrieved_config.name, "test_plugin");
    EXPECT_EQ(retrieved_config.model_path, "test_model.onnx");
    EXPECT_EQ(retrieved_config.batch_size, 1);
    
    // 测试所有配置获取
    auto all_configs = config_manager.getAllConfigs();
    EXPECT_EQ(all_configs.size(), 1);
    
    // 测试配置验证
    EXPECT_TRUE(config_manager.validateConfig(config));
    
    // 测试无效配置
    config.name = "";
    EXPECT_FALSE(config_manager.validateConfig(config));
}

// 测试插件生命周期管理器
TEST_F(PluginManagerTest, PluginLifecycleManager) {
    auto plugin_manager = std::make_shared<PluginManager>("test_plugins/");
    auto config_manager = std::make_shared<PluginConfigManager>("test_config.yaml");
    
    PluginLifecycleManager lifecycle_manager(plugin_manager, config_manager);
    
    // 注册插件
    auto factory = []() -> std::shared_ptr<IPlugin> {
        return std::make_shared<MockPlugin>();
    };
    
    plugin_manager->registerPlugin("mock_plugin", factory);
    
    // 设置配置
    PluginConfig config;
    config.name = "mock_plugin";
    config.model_path = "test_model.onnx";
    config.batch_size = 1;
    
    config_manager->setPluginConfig("mock_plugin", config);
    
    // 测试插件初始化
    EXPECT_TRUE(lifecycle_manager.initializePlugin("mock_plugin"));
    
    // 测试插件状态
    auto plugin = plugin_manager->getPlugin("mock_plugin");
    ASSERT_NE(plugin, nullptr);
    EXPECT_TRUE(plugin->isInitialized());
    
    // 测试插件关闭
    EXPECT_TRUE(lifecycle_manager.shutdownPlugin("mock_plugin"));
    EXPECT_FALSE(plugin->isInitialized());
    
    // 测试插件重启
    EXPECT_TRUE(lifecycle_manager.restartPlugin("mock_plugin"));
    EXPECT_TRUE(plugin->isInitialized());
    
    // 测试批量操作
    EXPECT_TRUE(lifecycle_manager.initializeAllPlugins());
    EXPECT_TRUE(lifecycle_manager.shutdownAllPlugins());
    EXPECT_TRUE(lifecycle_manager.restartAllPlugins());
}

// 测试插件发现器
TEST_F(PluginManagerTest, PluginDiscoverer) {
    PluginDiscoverer discoverer;
    
    // 添加插件路径
    discoverer.addPluginPath("test_plugins/");
    
    // 测试插件发现
    auto plugins = discoverer.discoverPlugins();
    // 这里应该有实际的插件文件才能测试
    
    // 测试插件验证
    // 这里应该有实际的插件文件才能测试
    
    // 测试插件信息获取
    // 这里应该有实际的插件文件才能测试
}

// 测试插件加载器
TEST_F(PluginManagerTest, PluginLoader) {
    PluginLoader loader;
    
    // 测试插件加载
    // 这里应该有实际的插件文件才能测试
    
    // 测试插件卸载
    // 这里应该有实际的插件文件才能测试
    
    // 测试已加载插件列表
    auto loaded_plugins = loader.getLoadedPlugins();
    EXPECT_TRUE(loaded_plugins.empty());
    
    // 测试插件状态检查
    EXPECT_FALSE(loader.isPluginLoaded("nonexistent_plugin"));
}

} // namespace v8_ai