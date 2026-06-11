@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 TeamRobert 智能缓存机制 - 快速启动
echo ============================================================
echo.

echo 【步骤1】诊断数据库状态...
python diagnose_db.py
if errorlevel 1 (
    echo ❌ 诊断发现问题
    pause
    exit /b 1
)
echo.

echo 【步骤2】修复并初始化团队成员数据...
python fix_and_init_members.py
if errorlevel 1 (
    echo ❌ 初始化失败
    pause
    exit /b 1
)
echo.

echo 【步骤3】测试缓存机制...
python test_cache.py
if errorlevel 1 (
    echo ❌ 测试失败
    pause
    exit /b 1
)
echo.

echo ============================================================
echo ✅ 准备完成！
echo ============================================================
echo.
echo 现在可以启动后端服务：
echo   python backend\main.py
echo.
echo 然后打开前端页面测试对话功能
echo.
pause
