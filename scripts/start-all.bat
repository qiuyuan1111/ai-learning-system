@echo off
REM Windows 一键启动人员 C 的服务（开发模式）
REM 双击运行 或 cmd 中执行 scripts\start-all.bat
setlocal
set ROOT=%~dp0..
set PY=python

echo === 个性化学习系统（人员 C 服务）开发环境 ===
%PY% --version

echo [0/3] 安装/更新 Python 共享库...
pushd "%ROOT%\common\python"
%PY% -m pip install -e . -q
popd

echo [1/3] 启动 resource-gen (端口 8090)...
start "resource-gen" cmd /k "cd /d %ROOT%\agents\resource-gen && %PY% -m uvicorn src.main:app --host 0.0.0.0 --port 8090"

echo [2/3] 启动 path-planner (端口 8091)...
start "path-planner" cmd /k "cd /d %ROOT%\agents\path-planner && %PY% -m uvicorn src.main:app --host 0.0.0.0 --port 8091"

echo [3/3] 已在新窗口启动两个服务。
echo   resource-gen : http://localhost:8090/docs
echo   path-planner : http://localhost:8091/docs
echo 关闭对应窗口即可停止服务。
endlocal
