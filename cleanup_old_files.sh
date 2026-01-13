#!/bin/bash
# 清理舊檔案腳本
# 執行前請確認已備份

echo "====================================="
echo "  清理舊檔案"
echo "====================================="

cd "$(dirname "$0")"

# 要刪除的 Python 模組
OLD_MODULES=(
    "gui_main.py"
    "archive_manager.py"
    "config_service.py"
    "diagnostics_manager.py"
    "download_manager.py"
    "enhanced_search_manager.py"
    "error_handler.py"
    "image_generation_okokgo.py"
    "improved_system_prompt.py"
    "install.py"
    "install.sh"
    "logging_service.py"
    "main.py"
    "monitoring_manager.py"
    "natural_language_search.py"
    "performance_monitor.py"
    "query_parser.py"
    "run_all_tests.py"
    "setup.sh"
    "start_windows.bat"
    "test_transcription_feature.py"
    "transcription_manager.py"
    "ui_components.py"
    "update_manager.py"
    "preprocessing_analysis_demo.py"
    "presentation_outline.txt"
    "version.json"
)

# 要刪除的文件
OLD_DOCS=(
    "AI_DETAILED_SPECIFICATIONS.md"
    "CHANGELOG.md"
    "DEVELOPMENT_WORKFLOW.md"
    "PROJECT_STRUCTURE.md"
    "TROUBLESHOOTING.md"
)

# 要刪除的目錄
OLD_DIRS=(
    "docs"
    "tests"
    "samples"
    "screenshots"
    "ui"
    "tmp-home"
    ".kiro"
    ".pytest_cache"
    "__pycache__"
)

echo ""
echo "將刪除以下檔案："
echo "----------------"

for file in "${OLD_MODULES[@]}"; do
    if [ -f "$file" ]; then
        echo "  📄 $file"
    fi
done

for file in "${OLD_DOCS[@]}"; do
    if [ -f "$file" ]; then
        echo "  📄 $file"
    fi
done

for dir in "${OLD_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  📁 $dir/"
    fi
done

echo ""
read -p "確定要刪除這些檔案嗎？(y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "已取消"
    exit 0
fi

# 刪除檔案
for file in "${OLD_MODULES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✅ 已刪除 $file"
    fi
done

for file in "${OLD_DOCS[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✅ 已刪除 $file"
    fi
done

# 刪除目錄
for dir in "${OLD_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "  ✅ 已刪除 $dir/"
    fi
done

# 刪除 macOS 隱藏檔案
find . -name "._*" -delete 2>/dev/null
echo "  ✅ 已清理 macOS 隱藏檔案"

echo ""
echo "====================================="
echo "  清理完成！"
echo "====================================="
echo ""
echo "保留的檔案："
echo "  📄 app_main.py          - 主程式"
echo "  📄 model_downloader.py  - 模型下載器"
echo "  📄 transcription_core.py- 轉錄核心"
echo "  📄 platform_adapter.py  - 跨平台適配器"
echo "  📄 requirements.txt     - 依賴清單"
echo "  📄 README.md            - 說明文件"
echo "  📄 LICENSE              - 授權條款"
echo "  📄 start.sh / start.bat - 啟動腳本"
echo "  📁 build_scripts/       - 打包腳本"
echo "  📁 whisper_resources/   - Whisper 資源"
