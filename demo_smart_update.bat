@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 智能对话式修改功能 - 快速演示
echo ============================================================
echo.

echo 【步骤 1】检查数据库...
python complete_fix.py
if errorlevel 1 (
    echo ❌ 数据库修复失败
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 【步骤 2】运行测试脚本
echo ============================================================
echo.

python test_smart_update.py

echo.
echo ============================================================
echo 🎉 演示完成！
echo ============================================================
echo.
echo 💡 下一步:
echo    1. 启动后端服务: cd backend ^&^& python main.py
echo    2. 打开前端页面: frontend/index.html
echo    3. 尝试以下指令:
echo       - "把张三的任务改成已完成"
echo       - "把所有待办任务改为进行中"
echo       - "查看任务列表"
echo.
echo 📖 详细文档: SMART_UPDATE_GUIDE.md
echo.

pause
