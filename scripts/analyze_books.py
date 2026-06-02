"""
分析书籍目录结构 - 从每个类别采样书籍分析数据特征
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import os
from pathlib import Path

root = Path('C:/Users/huiya/Desktop/books')
categories = sorted([d for d in root.iterdir() if d.is_dir()])

print(f'=== books 目录结构 (共 {len(categories)} 个类别) ===')
for d in categories:
    items = list(d.iterdir())
    files = [f for f in items if f.is_file() and f.suffix.lower() in ('.txt', '.pdf')]
    subdirs = [f for f in items if f.is_dir()]
    print(f'  [{d.name}] {len(items)} 项 (文件:{len(files)}, 子目录:{len(subdirs)})')
    
    # 采样前几个文件
    samples = []
    if files:
        samples = files[:3]
        for f in files[:3]:
            try:
                size = f.stat().st_size
                samples.append((f.name, size))
            except:
                pass
    
print(f'\n=== 采样文件详情 ===')

# 采样每个类别前5个文件
for d in categories:
    items = list(d.iterdir())
    files = [f for f in items if f.is_file() and f.suffix.lower() in ('.txt', '.pdf')]
    subdirs = [f for f in items if f.is_dir()]
    
    # 收集实际要读取的文件
    targets = []
    if files:
        targets = files[:3]
    elif subdirs:
        # 从子目录中找txt文件
        for sd in subdirs[:3]:
            inner = list(sd.iterdir())
            txts = [f for f in inner if f.is_file() and f.suffix.lower() in ('.txt', '.pdf')]
            if txts:
                targets.append(txts[0])
    
    if not targets:
        continue
    
    print(f'\n--- 类别 [{d.name}] ---')
    for f in targets[:3]:
        try:
            size = f.stat().st_size
            size_str = f'{size/1024:.0f}KB' if size < 1024*1024 else f'{size/1024/1024:.1f}MB'
            
            # 读取前500字符分析
            with open(f, 'r', encoding='utf-8', errors='replace') as fh:
                head = fh.read(1000)
            
            lines = head.split('\n')
            print(f'  文件: {f.name} ({size_str})')
            print(f'    前10行: {lines[:10]}')
            print(f'    总行数估计: 文件头占{len(head)}字符')
            # 检测是否有章节标记
            import re
            chapter_markers = re.findall(r'第[一二三四五六七八九十百千零\d]+[章篇节部]', head)
            if chapter_markers:
                print(f'    章节标记: {chapter_markers[:3]}...')
            else:
                print(f'    章节标记: 无')
        except Exception as e:
            print(f'  文件: {f.name} (读取失败: {e})')

print('\n=== 分析完成 ===')