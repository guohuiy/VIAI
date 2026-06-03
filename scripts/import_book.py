"""
批量导入电子书脚本
支持从分类目录结构扫描导入（如 C:/books/历史军事/xxx.txt）

用法：
  python scripts/import_book.py                          # 扫描 data/raw_books/
  python scripts/import_book.py --dir "C:/books/文学"    # 指定目录
  python scripts/import_book.py --full-scan              # 扫描 C:/books 全部分类
  python scripts/import_book.py --list                   # 列出已导入书籍
  python scripts/import_book.py --reindex                # 重新导入（覆盖旧数据）
  python scripts/import_book.py --skip-existing           # 跳过已存在的
"""

import argparse
import io
import sys
from pathlib import Path

# Windows GBK 编码兼容：设置标准输出为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.config import STORAGE_CONFIG  # noqa: E402, I001
from services.book_service import BookService, compute_file_hash, infer_category_from_path  # noqa: E402, I001

# 如果指定了 --full-scan，从该根目录扫描
DEFAULT_BOOKS_ROOT = Path(r"C:\Users\huiya\Desktop\books")


def scan_books_directory(scan_dir: Path, category_filter: str = None):
    """
    扫描目录结构，返回 (book_info_list, categories)
    - 如果 scan_dir 包含多个子目录（如 C:/books/下的23个分类目录）
      则视为分类根目录
    - 如果 scan_dir 是单个目录（如 C:/books/幽默笑话/）
      则视为单分类目录
    """
    all_books = []  # [(file_path, category)]

    # 判断是分类根目录还是单目录
    subdirs = [d for d in scan_dir.iterdir() if d.is_dir()]

    if len(subdirs) > 1:
        # 分类根目录模式
        print(f"  检测到分类根目录，包含 {len(subdirs)} 个子分类")
        for subdir in sorted(subdirs):
            cat_name = subdir.name
            if category_filter and cat_name != category_filter:
                continue
            files = [f for f in subdir.rglob("*") if f.is_file() and f.suffix.lower() in (".txt", ".pdf")]
            for f in files:
                all_books.append((f, cat_name))
    else:
        # 单目录模式
        cat_name = category_filter or scan_dir.name
        files = [f for f in scan_dir.rglob("*") if f.is_file() and f.suffix.lower() in (".txt", ".pdf")]
        for f in files:
            all_books.append((f, cat_name))

    categories = sorted(set(c for _, c in all_books))
    return all_books, categories


def main():
    parser = argparse.ArgumentParser(description="批量导入电子书到 ebook-content-studio")
    parser.add_argument(
        "files",
        nargs="*",
        help="要导入的电子书文件路径（支持 .txt, .pdf）",
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=STORAGE_CONFIG["raw_books"],
        help=f"批量导入目录中的电子书（默认: {STORAGE_CONFIG['raw_books']}）",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help=f"全量扫描 books 分类目录（默认从 {DEFAULT_BOOKS_ROOT} 扫描所有分类）",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="分类过滤（如：历史军事、幽默笑话），与 --full-scan 或 --dir 配合使用",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出已导入的书籍",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="重新导入已存在的书籍（删除旧数据后重新导入）",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="跳过已存在的书籍（默认：全部导入，可能重复）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅扫描不导入，预览会处理哪些文件",
    )

    args = parser.parse_args()
    service = BookService()

    if args.list:
        books = service.list_books()
        if not books:
            print("📚 暂无已导入的书籍")
            return
        print(f"\n📚 已导入的书籍 ({len(books)} 本):\n")
        for book in books:
            cat_tag = f"[{book.get('category','?')}]" if book.get('category') else ""
            print(f"  {cat_tag} [{book['id'][:8]}] {book['title']} "
                  f"({book['total_chunks']} 分块, {book['total_chars']} 字符, "
                  f"{book.get('language','?')})")
        # 分类汇总
        cats = {}
        for b in books:
            c = b.get('category', '未分类')
            cats[c] = cats.get(c, 0) + 1
        print("\n分类统计:")
        for c, n in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {c}: {n} 本")
        return

    # 收集要导入的文件列表
    files_to_import = []  # [(file_path_str, category)]
    categories = set()

    # 模式1：指定文件
    if args.files:
        for f in args.files:
            p = Path(f)
            if p.exists():
                cat = infer_category_from_path(str(p))
                files_to_import.append((str(p.resolve()), cat))
                if cat:
                    categories.add(cat)
            else:
                print(f"  ⚠️  文件不存在: {f}")

    # 模式2：全量扫描 books 目录
    elif args.full_scan:
        print(f"🔍 全量扫描: {DEFAULT_BOOKS_ROOT}")
        my_books, my_cats = scan_books_directory(DEFAULT_BOOKS_ROOT, args.category)
        for f, c in my_books:
            files_to_import.append((str(f.resolve()), c))
            categories.add(c)
        print(f"  扫描到 {len(files_to_import)} 个文件，{len(categories)} 个分类")
        for c in sorted(categories):
            count = sum(1 for _, cc in my_books if cc == c)
            print(f"    {c}: {count} 本")

    # 模式3：指定目录
    else:
        scan_path = Path(args.dir)
        if not scan_path.exists():
            print(f"❌ 目录不存在: {scan_path}")
            return
        # 判断是不是分类根目录
        subdirs = [d for d in scan_path.iterdir() if d.is_dir()]
        if len(subdirs) > 1:
            # 是分类根目录
            print(f"🔍 扫描分类目录: {scan_path}")
            my_books, my_cats = scan_books_directory(scan_path, args.category)
            for f, c in my_books:
                files_to_import.append((str(f.resolve()), c))
                categories.add(c)
        else:
            # 单目录
            print(f"🔍 扫描目录: {scan_path}")
            files = [
                str(f) for f in scan_path.rglob("*")
                if f.suffix.lower() in (".txt", ".pdf") and f.is_file()
            ]
            for f in files:
                cat = infer_category_from_path(f) or args.category or ""
                files_to_import.append((f, cat))
                categories.add(cat)

    if not files_to_import:
        print("❌ 未找到需要导入的电子书文件")
        parser.print_help()
        return

    # Dry-run 模式：只看不导入
    if args.dry_run:
        print(f"\n🔍 预览模式: 将处理 {len(files_to_import)} 个文件")
        print("\n分类分布:")
        cat_counts = {}
        for _, c in files_to_import:
            cat_counts[c] = cat_counts.get(c, 0) + 1
        for c, n in sorted(cat_counts.items(), key=lambda x: -x[1]):
            print(f"  {c or '未分类'}: {n} 本")
        print(f"\n共 {len(files_to_import)} 本，涉及 {len(categories)} 个分类")
        print("(添加 --dry-run 可移除，实际执行导入)")
        if len(files_to_import) > 20:
            print("\n前10本预览:")
            for f, c in files_to_import[:10]:
                print(f"  [{c}] {Path(f).name}")
        return

    # 正式导入
    existing_books = service.list_books()
    existing_hashes = {b.get("file_hash", "") for b in existing_books if b.get("file_hash")}
    existing_paths = {b["file_path"] for b in existing_books}

    skipped = 0
    reindexed = 0
    imported = 0
    errors = 0

    print(f"\n📖 开始导入 {len(files_to_import)} 个文件...\n")

    for idx, (file_path, category) in enumerate(files_to_import):
        p = Path(file_path)
        if not p.exists():
            print(f"  [{idx+1}/{len(files_to_import)}] ⚠️  文件不存在: {file_path}")
            errors += 1
            continue

        resolved = str(p.resolve())

        # 去重检查（MD5 + 路径双重检查）
        file_md5 = compute_file_hash(resolved)
        is_duplicate = (
            (args.skip_existing or not args.reindex) and
            (file_md5 in existing_hashes or resolved in existing_paths)
        )

        if is_duplicate:
            if args.reindex:
                # 删除旧记录
                for b in existing_books:
                    if b.get("file_hash") == file_md5 or b["file_path"] == resolved:
                        service.delete_book(b["id"])
                        existing_hashes.discard(file_md5)
                        existing_paths.discard(resolved)
                        reindexed += 1
                        break
                print(f"  [{idx+1}/{len(files_to_import)}] 🔄 重新导入: [{category}] {p.name}...", end=" ")
            elif args.skip_existing:
                print(f"  [{idx+1}/{len(files_to_import)}] ⏭️  跳过: [{category}] {p.name}（已存在）")
                skipped += 1
                continue
            else:
                print(f"  [{idx+1}/{len(files_to_import)}] ⚠️  已存在但未加 --reindex，跳过: {p.name}")
                skipped += 1
                continue
        else:
            print(f"  [{idx+1}/{len(files_to_import)}] 📖 正在处理: [{category}] {p.name}...", end=" ")

        try:
            result = service.import_book(resolved, category=category, compute_vector=False)
            if result.get("status") == "success":
                imported += 1
                existing_hashes.add(file_md5)
                existing_paths.add(resolved)
                lang_tag = f" [{result.get('language','?')}]" if result.get('language') else ""
                print(f"✅ 完成 ({result['total_chunks']} 分块, {result['total_chars']} 字符{lang_tag})")
            else:
                errors += 1
                print(f"❌ 失败: {result.get('error', '未知错误')}")
        except Exception as e:
            errors += 1
            print(f"❌ 异常: {str(e)}")

    # 最终统计
    print(f"\n{'='*50}")
    print("📊 导入完成统计")
    print(f"{'='*50}")
    print(f"  成功: {imported} 本")
    print(f"  跳过: {skipped} 本")
    print(f"  重新导入: {reindexed} 本")
    print(f"  失败: {errors} 本")
    if imported > 0 or reindexed > 0:
        print("\n💡 提示: 如需重建向量索引，请运行 python scripts/build_index.py")


if __name__ == "__main__":
    main()
