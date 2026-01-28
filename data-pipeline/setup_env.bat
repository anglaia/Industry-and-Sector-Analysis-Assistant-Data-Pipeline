@echo off
REM Setup data-pipeline environment variables
REM 自动从 backend-node/.env 复制 AWS 配置到 data-pipeline/.env

echo ========================================
echo 配置 data-pipeline 环境变量
echo ========================================
echo.

REM 检查 backend-node/.env 是否存在
if not exist "..\backend-node\.env" (
    echo ❌ 错误: 找不到 backend-node\.env
    echo    请先配置 backend-node\.env 文件
    pause
    exit /b 1
)

REM 检查 backend-ai/.env 是否存在
if not exist "..\backend-ai\.env" (
    echo ❌ 错误: 找不到 backend-ai\.env
    echo    请先配置 backend-ai\.env 文件
    pause
    exit /b 1
)

echo ✅ 找到配置文件:
echo    - backend-node\.env
echo    - backend-ai\.env
echo.

REM 创建或覆盖 .env 文件
echo # ========== AWS S3 配置（从 backend-node\.env 复制）========== > .env

REM 从 backend-node/.env 提取 AWS 配置
for /f "usebackq tokens=1,* delims==" %%a in ("..\backend-node\.env") do (
    set "line=%%a"
    if "!line:~0,4!"=="AWS_" (
        echo %%a=%%b >> .env
    )
)

echo. >> .env
echo # ========== AI 配置（从 backend-ai\.env 复制）========== >> .env

REM 从 backend-ai/.env 提取 AI 配置
for /f "usebackq tokens=1,* delims==" %%a in ("..\backend-ai\.env") do (
    set "line=%%a"
    REM Google API
    if "!line:~0,10!"=="GOOGLE_API" (
        echo %%a=%%b >> .env
    )
    REM Pinecone
    if "!line:~0,8!"=="PINECONE" (
        echo %%a=%%b >> .env
    )
)

echo.
echo ✅ 配置完成! .env 文件已创建
echo.
echo 📋 下一步:
echo    1. 查看 .env 文件确认配置正确
echo    2. 运行: python import_s3_to_pinecone.py --preview-only
echo    3. 运行: python import_s3_to_pinecone.py
echo.
pause

