#pragma once

#include <vector>
#include <memory>
#include <mutex>
#include <chrono>
#include <unordered_map>
#include <functional>

namespace v8_ai {

// 设备类型枚举
enum class DeviceType {
    CPU,
    GPU,
    AUTO
};

// 内存块信息
struct MemoryBlock {
    void* ptr;
    size_t size;
    bool isLocked;
    bool isPinned;  // CPU 内存是否锁定
    std::chrono::steady_clock::time_point lastUsed;
    DeviceType device;
    std::string tag;  // 内存块标签，用于调试
    
    MemoryBlock(void* p, size_t s, DeviceType d, const std::string& t = "")
        : ptr(p), size(s), isLocked(false), isPinned(false), 
          lastUsed(std::chrono::steady_clock::now()), device(d), tag(t) {}
};

// 内存分配策略
enum class AllocationStrategy {
    FIRST_FIT,    // 第一个合适的块
    BEST_FIT,     // 最佳匹配块
    WORST_FIT,    // 最差匹配块
    BUDDY_SYSTEM  // 伙伴系统
};

// 内存池配置
struct MemoryPoolConfig {
    size_t initial_pool_size = 1024 * 1024 * 1024;  // 1GB 初始池大小
    size_t max_pool_size = 4 * 1024 * 1024 * 1024;   // 4GB 最大池大小
    size_t min_block_size = 4096;                    // 最小块大小 4KB
    size_t max_block_size = 256 * 1024 * 1024;       // 最大块大小 256MB
    AllocationStrategy strategy = AllocationStrategy::BEST_FIT;
    bool enable_defragmentation = true;
    bool enable_statistics = true;
    size_t defragmentation_threshold = 100;  // 碎片化阈值
};

// 内存统计信息
struct MemoryStatistics {
    size_t total_allocated = 0;
    size_t total_free = 0;
    size_t peak_usage = 0;
    size_t allocation_count = 0;
    size_t deallocation_count = 0;
    size_t fragmentation_count = 0;
    double fragmentation_ratio = 0.0;
    
    void reset() {
        total_allocated = 0;
        total_free = 0;
        peak_usage = 0;
        allocation_count = 0;
        deallocation_count = 0;
        fragmentation_count = 0;
        fragmentation_ratio = 0.0;
    }
};

// 内存池基类
class MemoryPool {
protected:
    std::vector<MemoryBlock> blocks_;
    std::mutex mutex_;
    MemoryPoolConfig config_;
    MemoryStatistics stats_;
    
    // 内存分配策略
    virtual void* allocateStrategy(size_t size, DeviceType device) = 0;
    virtual void deallocateStrategy(void* ptr) = 0;
    
    // 内存管理
    virtual bool canAllocate(size_t size, DeviceType device) const = 0;
    virtual void* allocateNewBlock(size_t size, DeviceType device) = 0;
    virtual void freeBlock(MemoryBlock& block) = 0;
    
    // 碎片整理
    virtual void defragment() = 0;
    
public:
    MemoryPool(const MemoryPoolConfig& config) : config_(config) {}
    virtual ~MemoryPool() = default;
    
    // 分配内存
    virtual void* allocate(size_t size, DeviceType device = DeviceType::AUTO, 
                          const std::string& tag = "") = 0;
    
    // 释放内存
    virtual void deallocate(void* ptr) = 0;
    
    // 重新分配内存
    virtual void* reallocate(void* ptr, size_t new_size) = 0;
    
    // 获取统计信息
    virtual MemoryStatistics getStatistics() const = 0;
    
    // 重置统计
    virtual void resetStatistics() = 0;
    
    // 内存池大小
    virtual size_t getTotalSize() const = 0;
    virtual size_t getFreeSize() const = 0;
    virtual size_t getUsedSize() const = 0;
    
    // 设备信息
    virtual bool isDeviceSupported(DeviceType device) const = 0;
    virtual size_t getDeviceMemory(DeviceType device) const = 0;
};

// CPU 内存池实现
class CPUMemoryPool : public MemoryPool {
private:
    std::unordered_map<void*, MemoryBlock*> allocated_blocks_;
    
    void* allocateStrategy(size_t size, DeviceType device) override;
    void deallocateStrategy(void* ptr) override;
    
    bool canAllocate(size_t size, DeviceType device) const override;
    void* allocateNewBlock(size_t size, DeviceType device) override;
    void freeBlock(MemoryBlock& block) override;
    
    void defragment() override;
    
public:
    CPUMemoryPool(const MemoryPoolConfig& config);
    ~CPUMemoryPool();
    
    void* allocate(size_t size, DeviceType device = DeviceType::CPU, 
                  const std::string& tag = "") override;
    void deallocate(void* ptr) override;
    void* reallocate(void* ptr, size_t new_size) override;
    
    MemoryStatistics getStatistics() const override;
    void resetStatistics() override;
    
    size_t getTotalSize() const override;
    size_t getFreeSize() const override;
    size_t getUsedSize() const override;
    
    bool isDeviceSupported(DeviceType device) const override;
    size_t getDeviceMemory(DeviceType device) const override;
    
    // CPU 特定功能
    void* allocatePinned(size_t size, const std::string& tag = "");
    void deallocatePinned(void* ptr);
};

// GPU 内存池实现
class GPUMemoryPool : public MemoryPool {
private:
    std::unordered_map<void*, MemoryBlock*> allocated_blocks_;
    
    void* allocateStrategy(size_t size, DeviceType device) override;
    void deallocateStrategy(void* ptr) override;
    
    bool canAllocate(size_t size, DeviceType device) const override;
    void* allocateNewBlock(size_t size, DeviceType device) override;
    void freeBlock(MemoryBlock& block) override;
    
    void defragment() override;
    
public:
    GPUMemoryPool(const MemoryPoolConfig& config);
    ~GPUMemoryPool();
    
    void* allocate(size_t size, DeviceType device = DeviceType::GPU, 
                  const std::string& tag = "") override;
    void deallocate(void* ptr) override;
    void* reallocate(void* ptr, size_t new_size) override;
    
    MemoryStatistics getStatistics() const override;
    void resetStatistics() override;
    
    size_t getTotalSize() const override;
    size_t getFreeSize() const override;
    size_t getUsedSize() const override;
    
    bool isDeviceSupported(DeviceType device) const override;
    size_t getDeviceMemory(DeviceType device) const override;
    
    // GPU 特定功能
    bool copyHostToDevice(const void* host_ptr, void* device_ptr, size_t size);
    bool copyDeviceToHost(void* device_ptr, void* host_ptr, size_t size);
    bool copyDeviceToDevice(void* src_ptr, void* dst_ptr, size_t size);
};

// 统一内存池管理器
class UnifiedMemoryManager {
private:
    std::unique_ptr<CPUMemoryPool> cpu_pool_;
    std::unique_ptr<GPUMemoryPool> gpu_pool_;
    std::mutex mutex_;
    
    MemoryPoolConfig cpu_config_;
    MemoryPoolConfig gpu_config_;
    
public:
    UnifiedMemoryManager(const MemoryPoolConfig& cpu_config, 
                        const MemoryPoolConfig& gpu_config);
    ~UnifiedMemoryManager();
    
    // 内存分配
    void* allocate(size_t size, DeviceType device, const std::string& tag = "");
    void deallocate(void* ptr);
    void* reallocate(void* ptr, size_t new_size);
    
    // 内存拷贝
    bool copy(void* dst, const void* src, size_t size, 
             DeviceType dst_device, DeviceType src_device);
    
    // 统计信息
    MemoryStatistics getCPUStatistics() const;
    MemoryStatistics getGPUStatistics() const;
    void resetStatistics();
    
    // 内存池信息
    size_t getTotalMemory(DeviceType device) const;
    size_t getFreeMemory(DeviceType device) const;
    size_t getUsedMemory(DeviceType device) const;
    
    // 设备支持
    bool isDeviceSupported(DeviceType device) const;
    std::vector<DeviceType> getSupportedDevices() const;
    
    // 内存优化
    void optimizeMemoryUsage();
    void defragment(DeviceType device);
    
    // 内存池配置
    void updateConfig(const MemoryPoolConfig& config, DeviceType device);
    MemoryPoolConfig getConfig(DeviceType device) const;
};

// 内存分配器
template<typename T>
class MemoryAllocator {
private:
    UnifiedMemoryManager* memory_manager_;
    DeviceType device_;
    
public:
    using value_type = T;
    using pointer = T*;
    using const_pointer = const T*;
    using reference = T&;
    using const_reference = const T&;
    using size_type = std::size_t;
    using difference_type = std::ptrdiff_t;
    
    MemoryAllocator(UnifiedMemoryManager* manager, DeviceType device) 
        : memory_manager_(manager), device_(device) {}
    
    template<typename U>
    MemoryAllocator(const MemoryAllocator<U>& other) 
        : memory_manager_(other.memory_manager_), device_(other.device_) {}
    
    pointer allocate(size_type n) {
        return static_cast<pointer>(
            memory_manager_->allocate(n * sizeof(T), device_, "allocator")
        );
    }
    
    void deallocate(pointer p, size_type n) {
        memory_manager_->deallocate(p);
    }
    
    template<typename U>
    bool operator==(const MemoryAllocator<U>& other) const {
        return memory_manager_ == other.memory_manager_ && device_ == other.device_;
    }
    
    template<typename U>
    bool operator!=(const MemoryAllocator<U>& other) const {
        return !(*this == other);
    }
};

} // namespace v8_ai