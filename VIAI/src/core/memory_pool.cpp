#include "v8_core/memory_pool.h"
#include <iostream>
#include <algorithm>

namespace v8_ai {

// CPU 内存池实现
CPUMemoryPool::CPUMemoryPool(const MemoryPoolConfig& config) : MemoryPool(config) {
}

CPUMemoryPool::~CPUMemoryPool() {
    // 清理所有内存块
    for (auto& block : blocks_) {
        if (block.ptr) {
            free(block.ptr);
        }
    }
}

void* CPUMemoryPool::allocate(size_t size, DeviceType device, const std::string& tag) {
    if (device != DeviceType::CPU && device != DeviceType::AUTO) {
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 尝试分配策略
    void* ptr = allocateStrategy(size, device);
    if (ptr) {
        // 创建内存块记录
        MemoryBlock block(ptr, size, device, tag);
        blocks_.push_back(block);
        allocated_blocks_[ptr] = &blocks_.back();
        
        // 更新统计
        stats_.total_allocated += size;
        stats_.allocation_count++;
        stats_.peak_usage = std::max(stats_.peak_usage, stats_.total_allocated);
        
        return ptr;
    }
    
    // 策略失败，尝试分配新块
    ptr = allocateNewBlock(size, device);
    if (ptr) {
        MemoryBlock block(ptr, size, device, tag);
        blocks_.push_back(block);
        allocated_blocks_[ptr] = &blocks_.back();
        
        stats_.total_allocated += size;
        stats_.allocation_count++;
        stats_.peak_usage = std::max(stats_.peak_usage, stats_.total_allocated);
        
        return ptr;
    }
    
    return nullptr;
}

void CPUMemoryPool::deallocate(void* ptr) {
    if (!ptr) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = allocated_blocks_.find(ptr);
    if (it != allocated_blocks_.end()) {
        MemoryBlock& block = *it->second;
        
        // 标记为释放
        block.isLocked = false;
        block.lastUsed = std::chrono::steady_clock::now();
        
        // 更新统计
        stats_.total_allocated -= block.size;
        stats_.deallocation_count++;
        
        // 释放内存
        freeBlock(block);
        
        // 从映射中移除
        allocated_blocks_.erase(it);
    }
}

void* CPUMemoryPool::reallocate(void* ptr, size_t new_size) {
    if (!ptr) return allocate(new_size, DeviceType::CPU);
    if (new_size == 0) {
        deallocate(ptr);
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = allocated_blocks_.find(ptr);
    if (it != allocated_blocks_.end()) {
        MemoryBlock& block = *it->second;
        
        if (new_size <= block.size) {
            // 当前块足够大，不需要重新分配
            return ptr;
        }
        
        // 需要重新分配
        void* new_ptr = allocate(new_size, DeviceType::CPU, block.tag);
        if (new_ptr) {
            // 复制数据
            std::memcpy(new_ptr, ptr, block.size);
            
            // 释放旧内存
            deallocate(ptr);
            
            return new_ptr;
        }
    }
    
    return nullptr;
}

MemoryStatistics CPUMemoryPool::getStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return stats_;
}

void CPUMemoryPool::resetStatistics() {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_.reset();
}

size_t CPUMemoryPool::getTotalSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t total = 0;
    for (const auto& block : blocks_) {
        total += block.size;
    }
    return total;
}

size_t CPUMemoryPool::getFreeSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t free = 0;
    for (const auto& block : blocks_) {
        if (!block.isLocked) {
            free += block.size;
        }
    }
    return free;
}

size_t CPUMemoryPool::getUsedSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t used = 0;
    for (const auto& block : blocks_) {
        if (block.isLocked) {
            used += block.size;
        }
    }
    return used;
}

bool CPUMemoryPool::isDeviceSupported(DeviceType device) const {
    return device == DeviceType::CPU || device == DeviceType::AUTO;
}

size_t CPUMemoryPool::getDeviceMemory(DeviceType device) const {
    if (!isDeviceSupported(device)) {
        return 0;
    }
    
    // 获取系统总内存
    // 这里应该使用平台特定的API
    return getTotalSize();
}

void* CPUMemoryPool::allocatePinned(size_t size, const std::string& tag) {
    // 分配锁定内存（页面锁定内存）
    void* ptr = nullptr;
    
#ifdef _WIN32
    ptr = VirtualAlloc(nullptr, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (ptr) {
        VirtualLock(ptr, size);
    }
#else
    ptr = malloc(size);
    if (ptr) {
        mlock(ptr, size);
    }
#endif
    
    if (ptr) {
        MemoryBlock block(ptr, size, DeviceType::CPU, tag);
        block.isPinned = true;
        blocks_.push_back(block);
        allocated_blocks_[ptr] = &blocks_.back();
        
        stats_.total_allocated += size;
        stats_.allocation_count++;
    }
    
    return ptr;
}

void CPUMemoryPool::deallocatePinned(void* ptr) {
    if (!ptr) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = allocated_blocks_.find(ptr);
    if (it != allocated_blocks_.end()) {
        MemoryBlock& block = *it->second;
        if (block.isPinned) {
#ifdef _WIN32
            VirtualUnlock(ptr, block.size);
            VirtualFree(ptr, 0, MEM_RELEASE);
#else
            munlock(ptr, block.size);
            free(ptr);
#endif
            
            stats_.total_allocated -= block.size;
            stats_.deallocation_count++;
            
            allocated_blocks_.erase(it);
        }
    }
}

void* CPUMemoryPool::allocateStrategy(size_t size, DeviceType device) {
    if (config_.strategy == AllocationStrategy::FIRST_FIT) {
        return allocateFirstFit(size, device);
    } else if (config_.strategy == AllocationStrategy::BEST_FIT) {
        return allocateBestFit(size, device);
    } else if (config_.strategy == AllocationStrategy::WORST_FIT) {
        return allocateWorstFit(size, device);
    }
    
    return nullptr;
}

void CPUMemoryPool::deallocateStrategy(void* ptr) {
    deallocate(ptr);
}

bool CPUMemoryPool::canAllocate(size_t size, DeviceType device) const {
    return isDeviceSupported(device);
}

void* CPUMemoryPool::allocateNewBlock(size_t size, DeviceType device) {
    if (!canAllocate(size, device)) {
        return nullptr;
    }
    
    void* ptr = malloc(size);
    if (ptr) {
        stats_.total_allocated += size;
    }
    
    return ptr;
}

void CPUMemoryPool::freeBlock(MemoryBlock& block) {
    if (block.ptr) {
        free(block.ptr);
        block.ptr = nullptr;
    }
}

void CPUMemoryPool::defragment() {
    // CPU内存池的碎片整理
    // 这里可以实现内存压缩等策略
}

// GPU 内存池实现
GPUMemoryPool::GPUMemoryPool(const MemoryPoolConfig& config) : MemoryPool(config) {
}

GPUMemoryPool::~GPUMemoryPool() {
    // 清理所有GPU内存块
    for (auto& block : blocks_) {
        if (block.ptr) {
            cudaFree(block.ptr);
        }
    }
}

void* GPUMemoryPool::allocate(size_t size, DeviceType device, const std::string& tag) {
    if (device != DeviceType::GPU && device != DeviceType::AUTO) {
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    void* ptr = allocateStrategy(size, device);
    if (ptr) {
        MemoryBlock block(ptr, size, device, tag);
        blocks_.push_back(block);
        allocated_blocks_[ptr] = &blocks_.back();
        
        stats_.total_allocated += size;
        stats_.allocation_count++;
        stats_.peak_usage = std::max(stats_.peak_usage, stats_.total_allocated);
        
        return ptr;
    }
    
    ptr = allocateNewBlock(size, device);
    if (ptr) {
        MemoryBlock block(ptr, size, device, tag);
        blocks_.push_back(block);
        allocated_blocks_[ptr] = &blocks_.back();
        
        stats_.total_allocated += size;
        stats_.allocation_count++;
        stats_.peak_usage = std::max(stats_.peak_usage, stats_.total_allocated);
        
        return ptr;
    }
    
    return nullptr;
}

void GPUMemoryPool::deallocate(void* ptr) {
    if (!ptr) return;
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = allocated_blocks_.find(ptr);
    if (it != allocated_blocks_.end()) {
        MemoryBlock& block = *it->second;
        
        block.isLocked = false;
        block.lastUsed = std::chrono::steady_clock::now();
        
        stats_.total_allocated -= block.size;
        stats_.deallocation_count++;
        
        freeBlock(block);
        
        allocated_blocks_.erase(it);
    }
}

void* GPUMemoryPool::reallocate(void* ptr, size_t new_size) {
    if (!ptr) return allocate(new_size, DeviceType::GPU);
    if (new_size == 0) {
        deallocate(ptr);
        return nullptr;
    }
    
    std::lock_guard<std::mutex> lock(mutex_);
    
    auto it = allocated_blocks_.find(ptr);
    if (it != allocated_blocks_.end()) {
        MemoryBlock& block = *it->second;
        
        if (new_size <= block.size) {
            return ptr;
        }
        
        void* new_ptr = allocate(new_size, DeviceType::GPU, block.tag);
        if (new_ptr) {
            // 复制数据
            cudaMemcpy(new_ptr, ptr, block.size, cudaMemcpyDeviceToDevice);
            
            deallocate(ptr);
            
            return new_ptr;
        }
    }
    
    return nullptr;
}

MemoryStatistics GPUMemoryPool::getStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return stats_;
}

void GPUMemoryPool::resetStatistics() {
    std::lock_guard<std::mutex> lock(mutex_);
    stats_.reset();
}

size_t GPUMemoryPool::getTotalSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t total = 0;
    for (const auto& block : blocks_) {
        total += block.size;
    }
    return total;
}

size_t GPUMemoryPool::getFreeSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t free = 0;
    for (const auto& block : blocks_) {
        if (!block.isLocked) {
            free += block.size;
        }
    }
    return free;
}

size_t GPUMemoryPool::getUsedSize() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t used = 0;
    for (const auto& block : blocks_) {
        if (block.isLocked) {
            used += block.size;
        }
    }
    return used;
}

bool GPUMemoryPool::isDeviceSupported(DeviceType device) const {
    return device == DeviceType::GPU || device == DeviceType::AUTO;
}

size_t GPUMemoryPool::getDeviceMemory(DeviceType device) const {
    if (!isDeviceSupported(device)) {
        return 0;
    }
    
    size_t free = 0, total = 0;
    cudaMemGetInfo(&free, &total);
    
    return total;
}

bool GPUMemoryPool::copyHostToDevice(const void* host_ptr, void* device_ptr, size_t size) {
    return cudaMemcpy(device_ptr, host_ptr, size, cudaMemcpyHostToDevice) == cudaSuccess;
}

bool GPUMemoryPool::copyDeviceToHost(void* device_ptr, void* host_ptr, size_t size) {
    return cudaMemcpy(host_ptr, device_ptr, size, cudaMemcpyDeviceToHost) == cudaSuccess;
}

bool GPUMemoryPool::copyDeviceToDevice(void* src_ptr, void* dst_ptr, size_t size) {
    return cudaMemcpy(dst_ptr, src_ptr, size, cudaMemcpyDeviceToDevice) == cudaSuccess;
}

void* GPUMemoryPool::allocateStrategy(size_t size, DeviceType device) {
    // GPU内存分配策略
    return allocateBestFit(size, device);
}

void GPUMemoryPool::deallocateStrategy(void* ptr) {
    deallocate(ptr);
}

bool GPUMemoryPool::canAllocate(size_t size, DeviceType device) const {
    if (!isDeviceSupported(device)) {
        return false;
    }
    
    size_t free_memory = getFreeSize();
    return free_memory >= size;
}

void* GPUMemoryPool::allocateNewBlock(size_t size, DeviceType device) {
    if (!canAllocate(size, device)) {
        return nullptr;
    }
    
    void* ptr = nullptr;
    cudaError_t error = cudaMalloc(&ptr, size);
    
    if (error == cudaSuccess) {
        stats_.total_allocated += size;
    }
    
    return ptr;
}

void GPUMemoryPool::freeBlock(MemoryBlock& block) {
    if (block.ptr) {
        cudaFree(block.ptr);
        block.ptr = nullptr;
    }
}

void GPUMemoryPool::defragment() {
    // GPU内存池的碎片整理
    // 这里可以实现内存压缩等策略
}

// 统一内存管理器实现
UnifiedMemoryManager::UnifiedMemoryManager(const MemoryPoolConfig& cpu_config, 
                                         const MemoryPoolConfig& gpu_config) {
    cpu_pool_ = std::make_unique<CPUMemoryPool>(cpu_config);
    gpu_pool_ = std::make_unique<GPUMemoryPool>(gpu_config);
}

UnifiedMemoryManager::~UnifiedMemoryManager() {
}

void* UnifiedMemoryManager::allocate(size_t size, DeviceType device, const std::string& tag) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_pool_->allocate(size, device, tag);
    } else if (device == DeviceType::GPU) {
        return gpu_pool_->allocate(size, device, tag);
    } else if (device == DeviceType::AUTO) {
        // 自动选择最佳设备
        size_t cpu_free = cpu_pool_->getFreeSize();
        size_t gpu_free = gpu_pool_->getFreeSize();
        
        if (gpu_free >= size && gpu_free > cpu_free) {
            return gpu_pool_->allocate(size, DeviceType::GPU, tag);
        } else {
            return cpu_pool_->allocate(size, DeviceType::CPU, tag);
        }
    }
    
    return nullptr;
}

void UnifiedMemoryManager::deallocate(void* ptr) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 尝试在CPU池中查找
    if (cpu_pool_->isDeviceSupported(DeviceType::CPU)) {
        cpu_pool_->deallocate(ptr);
        return;
    }
    
    // 尝试在GPU池中查找
    if (gpu_pool_->isDeviceSupported(DeviceType::GPU)) {
        gpu_pool_->deallocate(ptr);
        return;
    }
}

void* UnifiedMemoryManager::reallocate(void* ptr, size_t new_size) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 尝试在CPU池中重新分配
    if (cpu_pool_->isDeviceSupported(DeviceType::CPU)) {
        void* new_ptr = cpu_pool_->reallocate(ptr, new_size);
        if (new_ptr) {
            return new_ptr;
        }
    }
    
    // 尝试在GPU池中重新分配
    if (gpu_pool_->isDeviceSupported(DeviceType::GPU)) {
        void* new_ptr = gpu_pool_->reallocate(ptr, new_size);
        if (new_ptr) {
            return new_ptr;
        }
    }
    
    return nullptr;
}

bool UnifiedMemoryManager::copy(void* dst, const void* src, size_t size, 
                              DeviceType dst_device, DeviceType src_device) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (dst_device == DeviceType::CPU && src_device == DeviceType::CPU) {
        std::memcpy(dst, src, size);
        return true;
    } else if (dst_device == DeviceType::GPU && src_device == DeviceType::CPU) {
        return gpu_pool_->copyHostToDevice(src, dst, size);
    } else if (dst_device == DeviceType::CPU && src_device == DeviceType::GPU) {
        return gpu_pool_->copyDeviceToHost(src, dst, size);
    } else if (dst_device == DeviceType::GPU && src_device == DeviceType::GPU) {
        return gpu_pool_->copyDeviceToDevice(src, dst, size);
    }
    
    return false;
}

MemoryStatistics UnifiedMemoryManager::getCPUStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return cpu_pool_->getStatistics();
}

MemoryStatistics UnifiedMemoryManager::getGPUStatistics() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return gpu_pool_->getStatistics();
}

void UnifiedMemoryManager::resetStatistics() {
    std::lock_guard<std::mutex> lock(mutex_);
    cpu_pool_->resetStatistics();
    gpu_pool_->resetStatistics();
}

size_t UnifiedMemoryManager::getTotalMemory(DeviceType device) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_pool_->getTotalSize();
    } else if (device == DeviceType::GPU) {
        return gpu_pool_->getTotalSize();
    }
    
    return 0;
}

size_t UnifiedMemoryManager::getFreeMemory(DeviceType device) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_pool_->getFreeSize();
    } else if (device == DeviceType::GPU) {
        return gpu_pool_->getFreeSize();
    }
    
    return 0;
}

size_t UnifiedMemoryManager::getUsedMemory(DeviceType device) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_pool_->getUsedSize();
    } else if (device == DeviceType::GPU) {
        return gpu_pool_->getUsedSize();
    }
    
    return 0;
}

bool UnifiedMemoryManager::isDeviceSupported(DeviceType device) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_pool_->isDeviceSupported(device);
    } else if (device == DeviceType::GPU) {
        return gpu_pool_->isDeviceSupported(device);
    }
    
    return false;
}

std::vector<DeviceType> UnifiedMemoryManager::getSupportedDevices() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<DeviceType> devices;
    
    if (cpu_pool_->isDeviceSupported(DeviceType::CPU)) {
        devices.push_back(DeviceType::CPU);
    }
    
    if (gpu_pool_->isDeviceSupported(DeviceType::GPU)) {
        devices.push_back(DeviceType::GPU);
    }
    
    return devices;
}

void UnifiedMemoryManager::optimizeMemoryUsage() {
    std::lock_guard<std::mutex> lock(mutex_);
    
    // 优化CPU内存使用
    cpu_pool_->defragment();
    
    // 优化GPU内存使用
    gpu_pool_->defragment();
}

void UnifiedMemoryManager::defragment(DeviceType device) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        cpu_pool_->defragment();
    } else if (device == DeviceType::GPU) {
        gpu_pool_->defragment();
    }
}

void UnifiedMemoryManager::updateConfig(const MemoryPoolConfig& config, DeviceType device) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        cpu_config_ = config;
        // 重新配置CPU内存池
    } else if (device == DeviceType::GPU) {
        gpu_config_ = config;
        // 重新配置GPU内存池
    }
}

MemoryPoolConfig UnifiedMemoryManager::getConfig(DeviceType device) const {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (device == DeviceType::CPU) {
        return cpu_config_;
    } else if (device == DeviceType::GPU) {
        return gpu_config_;
    }
    
    return MemoryPoolConfig{};
}

} // namespace v8_ai